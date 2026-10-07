import {
	type IExecuteFunctions,
	type INodeExecutionData,
	type INodeType,
	type INodeTypeDescription,
	type IRequestOptions,
	type NodeConnectionType,
	NodeConnectionTypes,
	NodeOperationError,
} from 'n8n-workflow';
import type { ScenarioContext } from '../ScenarioConfig/ScenarioConfig.node';

// ─────────────────────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────────────────────

interface ThenAction {
	next?: string;
	alarm?: string;
	message?: string;
	set_var?: unknown;
	set_loc?: string;
	set_pos?: unknown;
	release?: string[];
	max_retry?: number;
	wait_retry?: number;
	delay?: number;
}

interface RoutingCondition {
	label: string;
	when: string;         // 조건식 (비어있으면 default)
	thenJson: string;     // ThenAction[] JSON 직렬화
}

interface AcquireParam {
	roles?: {
		main?: string;
		sub1?: string;
		sub2?: string;
		sub3?: string;
	};
}

// ─────────────────────────────────────────────────────────────
// 템플릿 변수 해석
// ─────────────────────────────────────────────────────────────

/**
 * {{acq.main}}, {{res}}, {{var}}, {{loc}}, {{pos}} 등을 컨텍스트 값으로 치환
 */
function resolveTemplate(template: string, ctx: ScenarioContext): string {
	return template.replace(/\{\{([^}]+)\}\}/g, (match, key: string) => {
		const parts = key.trim().split('.');
		if (parts[0] === 'acq') {
			const role = parts[1];
			if (role === 'all') {
				return Object.values(ctx.acq).join(',');
			}
			return ctx.acq[role] ?? match;
		}
		if (parts[0] === 'res') return String(ctx.lastResponse ?? '');
		if (parts[0] === 'var') return String(ctx.var ?? '');
		if (parts[0] === 'loc') return String(ctx.loc ?? '');
		if (parts[0] === 'pos') return String(ctx.pos ?? '');
		return match;
	});
}

/**
 * 객체의 모든 string 값에 대해 템플릿 치환
 */
function resolveObject(obj: unknown, ctx: ScenarioContext): unknown {
	if (typeof obj === 'string') return resolveTemplate(obj, ctx);
	if (Array.isArray(obj)) return obj.map((v) => resolveObject(v, ctx));
	if (obj !== null && typeof obj === 'object') {
		const result: Record<string, unknown> = {};
		for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
			result[k] = resolveObject(v, ctx);
		}
		return result;
	}
	return obj;
}

// ─────────────────────────────────────────────────────────────
// 라우팅 조건 평가
// ─────────────────────────────────────────────────────────────

/**
 * when 조건식을 평가. 비어있으면 default (항상 true).
 * Python 스타일 True/False/None을 JS로 변환 후 평가.
 */
function evaluateCondition(when: string, ctx: ScenarioContext): boolean {
	const trimmed = when?.trim();
	if (!trimmed) return true; // default 조건

	const resolved = resolveTemplate(trimmed, ctx);
	const jsExpr = resolved
		.replace(/\bTrue\b/g, 'true')
		.replace(/\bFalse\b/g, 'false')
		.replace(/\bNone\b/g, 'null');

	try {
		// eslint-disable-next-line no-new-func
		return Boolean(new Function(`"use strict"; return (${jsExpr});`)());
	} catch {
		return false;
	}
}

// ─────────────────────────────────────────────────────────────
// Acquire / Release 처리
// ─────────────────────────────────────────────────────────────

/**
 * acquire 파라미터를 처리하여 컨텍스트 내 lock 상태와 acq 맵을 갱신
 */
function processAcquire(acquireParam: AcquireParam, ctx: ScenarioContext): void {
	const roles = acquireParam?.roles;
	if (!roles) return;

	const roleKeys = ['main', 'sub1', 'sub2', 'sub3'] as const;
	for (const role of roleKeys) {
		const assetIds = roles[role];
		if (!assetIds) continue;

		// 쉼표 구분 복수 자산 지원
		const ids = assetIds.split(',').map((s) => s.trim()).filter(Boolean);
		for (const id of ids) {
			if (ctx.assets[id]) {
				ctx.assets[id].locked = true;
			}
		}
		// acq.{role} 에는 첫 번째 자산의 name을 저장
		const firstName = ids[0] ? (ctx.assets[ids[0]]?.name ?? ids[0]) : '';
		ctx.acq[role] = firstName;
	}

	// 전역 lock 갱신
	ctx.lock = Object.values(ctx.assets).some((a) => a.locked);
}

/**
 * release 목록(["{{acq.main}}", "{{acq.sub1}}", "{{acq.all}}"]) 처리
 */
function processRelease(releaseList: string[], ctx: ScenarioContext): void {
	for (const raw of releaseList) {
		const resolved = resolveTemplate(raw, ctx);

		if (resolved.includes(',') || raw.includes('acq.all')) {
			// "acq.all" → 모든 자산 해제
			for (const asset of Object.values(ctx.assets)) {
				asset.locked = false;
			}
			ctx.acq = {};
		} else {
			// 특정 자산 이름으로 해제
			for (const asset of Object.values(ctx.assets)) {
				if (asset.name === resolved || asset.id === resolved) {
					asset.locked = false;
				}
			}
			// acq 맵에서도 제거
			for (const [role, name] of Object.entries(ctx.acq)) {
				if (name === resolved) {
					delete ctx.acq[role];
				}
			}
		}
	}

	// 전역 lock 갱신
	ctx.lock = Object.values(ctx.assets).some((a) => a.locked);
}

// ─────────────────────────────────────────────────────────────
// then 액션 처리
// ─────────────────────────────────────────────────────────────

/**
 * routing.then 액션 배열을 순서대로 처리하여 컨텍스트 갱신
 */
function processThenActions(actions: ThenAction[], ctx: ScenarioContext): void {
	for (const action of actions) {
		if (action.set_var !== undefined) {
			const val = action.set_var;
			ctx.var = typeof val === 'string' ? resolveTemplate(val, ctx) : val;
		}
		if (action.set_loc !== undefined) {
			ctx.loc = resolveTemplate(String(action.set_loc), ctx);
			ctx.pos = null; // set_loc 시 pos 초기화 (YAML 주석 명세)
		}
		if (action.set_pos !== undefined) {
			const val = action.set_pos;
			ctx.pos = typeof val === 'string' ? resolveTemplate(val, ctx) : val;
		}
		if (action.release) {
			processRelease(action.release, ctx);
		}
		// message, alarm, next, max_retry 등은 메타데이터로만 기록 (실제 흐름은 n8n 연결로)
	}
}

// ─────────────────────────────────────────────────────────────
// HTTP 메서드 결정
// ─────────────────────────────────────────────────────────────

function resolveHttpMethod(actionPath: string): 'GET' | 'POST' {
	if (actionPath.includes('/queries/') || actionPath.includes('/status/')) {
		return 'GET';
	}
	return 'POST'; // commands/
}

// ─────────────────────────────────────────────────────────────
// 노드 정의
// ─────────────────────────────────────────────────────────────

export class ScenarioStep implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Scenario Step',
		name: 'scenarioStep',
		icon: 'fa:play-circle',
		group: ['transform'],
		version: 1,
		description: '시나리오 YAML의 step 1개를 표현합니다. Acquire/Release, 템플릿 변수 해석, HTTP action 실행, 라우팅을 처리합니다.',
		defaults: {
			name: 'Scenario Step',
			color: '#FF6D5A',
		},
		inputs: [NodeConnectionTypes.Main],
		// 동적 출력: routing 조건 수만큼 출력 핀 생성
		outputs: `={{
			(() => {
				try {
					const routing = ($parameter["routing"] || {}).values || [];
					if (!routing || routing.length === 0) {
						return [{ type: "main", displayName: "Output" }];
					}
					return routing.map((r, i) => ({
						type: "main",
						displayName: r.label || (r.when ? r.when.substring(0, 22) : "Default")
					}));
				} catch(e) {
					return [{ type: "main", displayName: "Output" }];
				}
			})()
		}}`,
		properties: [
			// ── 기본 정보 ──────────────────────────────────────────
			{
				displayName: 'Step ID',
				name: 'stepId',
				type: 'string',
				default: '',
				placeholder: '1-1',
				description: 'YAML step의 id (예: 1-1, 2-3)',
				required: true,
			},
			{
				displayName: 'Step Name',
				name: 'stepName',
				type: 'string',
				default: '',
				placeholder: 'ANT: 홈 -> 소재공급기 이동',
				description: 'YAML step의 name',
			},

			// ── Acquire ────────────────────────────────────────────
			{
				displayName: 'Acquire Resources',
				name: 'acquire',
				type: 'fixedCollection',
				default: {},
				description: '이 step 시작 시 점유할 자산. YAML acquire 필드에 해당합니다. lock=true로 설정됩니다.',
				options: [
					{
						name: 'roles',
						displayName: 'Roles',
						values: [
							{
								displayName: 'Main',
								name: 'main',
								type: 'string',
								default: '',
								placeholder: 'ANT',
								description: '주 자산 ID (쉼표로 복수 지정 가능)',
							},
							{
								displayName: 'Sub1',
								name: 'sub1',
								type: 'string',
								default: '',
								placeholder: 'UR',
							},
							{
								displayName: 'Sub2',
								name: 'sub2',
								type: 'string',
								default: '',
								placeholder: 'CNC',
							},
							{
								displayName: 'Sub3',
								name: 'sub3',
								type: 'string',
								default: '',
								placeholder: 'FEEDER',
							},
						],
					},
				],
			},

			// ── Action ─────────────────────────────────────────────
			{
				displayName: 'Action',
				name: 'action',
				type: 'string',
				default: '',
				placeholder: '{{acq.main}}/robotGateway/commands/move',
				description: '실행할 AAS 오퍼레이션 경로. {{acq.main}}, {{acq.sub1}} 등 템플릿 변수 사용 가능.',
				required: true,
			},
			{
				displayName: 'Params (JSON)',
				name: 'paramsJson',
				type: 'string',
				typeOptions: { rows: 3 },
				default: '{}',
				description: 'action에 전달할 파라미터 JSON. {{var}}, {{pos}} 등 템플릿 변수 사용 가능.',
			},

			// ── Routing ────────────────────────────────────────────
			{
				displayName: 'Routing Conditions',
				name: 'routing',
				type: 'fixedCollection',
				typeOptions: {
					multipleValues: true,
					sortable: true,
				},
				default: { values: [] },
				description: 'action 응답에 따른 분기 조건. 각 조건이 출력 핀 1개에 대응합니다.',
				options: [
					{
						name: 'values',
						displayName: 'Condition',
						values: [
							{
								displayName: 'Output Pin Label',
								name: 'label',
								type: 'string',
								default: '',
								placeholder: 'OK 분기',
								description: '출력 핀에 표시될 이름',
							},
							{
								displayName: 'When (조건식)',
								name: 'when',
								type: 'string',
								default: '',
								placeholder: "'{{res}}' == 'OK'",
								description: '빈 값이면 Default(항상 매치). Python True/False 사용 가능.',
							},
							{
								displayName: 'Then Actions (JSON 배열)',
								name: 'thenJson',
								type: 'string',
								typeOptions: { rows: 4 },
								default: '[]',
								description: 'YAML then 블록을 JSON으로. 예: [{"set_var":"{{res}}"},{"next":"1-3"}]',
							},
						],
					},
				],
			},
		],
	};

	// ─────────────────────────────────────────────────────────
	// 실행 로직
	// ─────────────────────────────────────────────────────────

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const node = this.getNode();

		// 입력 데이터에서 scenarioContext 추출
		const inputJson = items[0]?.json ?? {};
		const ctx: ScenarioContext = (inputJson.scenarioContext as ScenarioContext) ?? {
			name: '',
			baseUrl: 'http://localhost:8080',
			assets: {},
			aas: null,
			acq: {},
			lock: false,
			var: null,
			loc: null,
			pos: null,
			lastResponse: null,
			stepHistory: [],
		};

		// 파라미터 읽기
		const stepId = this.getNodeParameter('stepId', 0) as string;
		const stepName = this.getNodeParameter('stepName', 0) as string;
		const acquireParam = this.getNodeParameter('acquire', 0) as AcquireParam;
		const action = this.getNodeParameter('action', 0) as string;
		const paramsJsonRaw = this.getNodeParameter('paramsJson', 0) as string;
		const routingParam = this.getNodeParameter('routing', 0) as { values?: RoutingCondition[] };
		const routingConditions = routingParam?.values ?? [];

		// step 이력 기록
		ctx.stepHistory = [...(ctx.stepHistory ?? []), stepId];

		// ① Acquire 처리 (이 step에 acquire가 있으면)
		if (acquireParam?.roles) {
			processAcquire(acquireParam, ctx);
		}

		// ② action URL 템플릿 해석
		const resolvedAction = resolveTemplate(action, ctx);
		const httpMethod = resolveHttpMethod(resolvedAction);
		const url = `${ctx.baseUrl}/${resolvedAction}`;

		// ③ params 해석
		let resolvedParams: Record<string, unknown> = {};
		try {
			const parsed = JSON.parse(paramsJsonRaw || '{}');
			resolvedParams = resolveObject(parsed, ctx) as Record<string, unknown>;
		} catch {
			// params 파싱 오류 시 빈 객체
		}

		// ④ HTTP 요청 실행
		let response: unknown = null;
		try {
			const requestOptions: IRequestOptions = {
				method: httpMethod,
				url,
				headers: { 'Content-Type': 'application/json' },
				json: true,
			};
			if (httpMethod === 'POST' && Object.keys(resolvedParams).length > 0) {
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				(requestOptions as any).body = resolvedParams;
			} else if (httpMethod === 'GET' && Object.keys(resolvedParams).length > 0) {
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				(requestOptions as any).qs = resolvedParams;
			}
			response = await this.helpers.request(requestOptions);
		} catch (err: unknown) {
			// HTTP 오류 시 응답 값으로 사용
			response = err instanceof Error ? err.message : String(err);
		}

		// lastResponse 업데이트
		ctx.lastResponse = response;

		// ⑤ 라우팅 조건 평가 → 매칭된 출력 핀으로 데이터 전달
		const outputs: INodeExecutionData[][] = routingConditions.map(() => []);
		if (outputs.length === 0) outputs.push([]);

		let matched = false;
		for (let i = 0; i < routingConditions.length; i++) {
			const cond = routingConditions[i];
			if (evaluateCondition(cond.when, ctx)) {
				// then 액션 처리 (set_var, set_loc, set_pos, release)
				let thenActions: ThenAction[] = [];
				try {
					thenActions = JSON.parse(cond.thenJson || '[]') as ThenAction[];
				} catch {
					// JSON 파싱 실패 시 무시
				}
				processThenActions(thenActions, ctx);

				// 경보/메시지 추출 (메타데이터로 전달)
				const alarmMsg = thenActions.find((a) => a.alarm)?.alarm ?? null;
				const message = thenActions.find((a) => a.message)?.message ?? null;
				const nextStepId = thenActions.find((a) => a.next)?.next ?? null;
				const maxRetry = thenActions.find((a) => a.max_retry !== undefined)?.max_retry ?? null;

				outputs[i] = [
					{
						json: {
							scenarioContext: ctx,
							_step: {
								id: stepId,
								name: stepName,
								action: resolvedAction,
								response,
								matchedConditionIndex: i,
								matchedWhen: cond.when,
								nextStepId,
								alarm: alarmMsg,
								message,
								maxRetry,
							},
						},
					},
				];
				matched = true;
				break; // 첫 번째 매칭 조건에서 중단
			}
		}

		// 매칭 조건 없을 때 첫 번째 출력으로 보냄
		if (!matched && outputs.length > 0) {
			outputs[0] = [
				{
					json: {
						scenarioContext: ctx,
						_step: {
							id: stepId,
							name: stepName,
							action: resolvedAction,
							response,
							matchedConditionIndex: -1,
							matchedWhen: null,
							nextStepId: null,
							alarm: `No routing condition matched for step ${stepId}`,
							message: null,
							maxRetry: null,
						},
					},
				},
			];
		}

		if (!matched && outputs.length === 0) {
			throw new NodeOperationError(node, `Step ${stepId}: routing conditions 없음`);
		}

		return outputs;
	}
}
