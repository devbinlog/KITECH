import {
	type IExecuteFunctions,
	type INodeExecutionData,
	type INodeType,
	type INodeTypeDescription,
	type NodeConnectionType,
	NodeConnectionTypes,
} from 'n8n-workflow';
import * as fs from 'fs';
import * as path from 'path';

/** 시나리오 전역 컨텍스트 타입 */
export interface ScenarioContext {
	name: string;
	baseUrl: string;
	/** 자산 ID(YAML) → 자산 정보 매핑 */
	assets: Record<string, { id: string; name: string; locked: boolean }>;
	/** AAS JSON 전체 데이터 (선택적) */
	aas: unknown;
	/** 현재 acquire된 역할별 자산 이름 매핑 { main: "ANT_ROBOT", sub1: "UR_ROBOT", ... } */
	acq: Record<string, string>;
	/** 전역 lock 상태: 어느 자산이라도 acquire되어 있으면 true */
	lock: boolean;
	/** set_var 로 설정되는 범용 변수 */
	var: unknown;
	/** set_loc 로 설정되는 현재 위치(자산) */
	loc: unknown;
	/** set_pos 로 설정되는 현재 포지션 */
	pos: unknown;
	/** 마지막 action의 응답 값 */
	lastResponse: unknown;
	/** 방문한 step ID 이력 (디버깅용) */
	stepHistory: string[];
}

export class ScenarioConfig implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Scenario Config',
		name: 'scenarioConfig',
		icon: 'fa:cog',
		group: ['transform'],
		version: 1,
		description: 'AAS 자산 파일을 읽어 시나리오 전역 컨텍스트를 초기화합니다. 워크플로우 맨 앞에 1번만 배치합니다.',
		defaults: {
			name: 'Scenario Config',
			color: '#1A82e2',
		},
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		properties: [
			{
				displayName: 'Scenario Name',
				name: 'scenarioName',
				type: 'string',
				default: '',
				placeholder: 'Cell1_Scenario_Linear',
				description: 'YAML 시나리오 파일의 name 필드',
				required: true,
			},
			{
				displayName: 'AAS File Path',
				name: 'aasFilePath',
				type: 'string',
				default: '/data/cell1_aas.json',
				description: '컨테이너 내부 AAS JSON 파일 경로 (예: /data/cell1_aas.json)',
			},
			{
				displayName: 'Asset API Base URL',
				name: 'baseUrl',
				type: 'string',
				default: 'http://localhost:8080',
				description: '자산 API 기본 URL. 각 step의 action은 {baseUrl}/{assetName}/{gateway}/{method} 형태로 호출됩니다.',
			},
			{
				displayName: 'Assets',
				name: 'assets',
				type: 'fixedCollection',
				typeOptions: {
					multipleValues: true,
					sortable: true,
				},
				default: { asset: [] },
				description: '시나리오에서 사용하는 자산 목록 (YAML의 assets 섹션)',
				options: [
					{
						name: 'asset',
						displayName: 'Asset',
						values: [
							{
								displayName: 'Asset ID (YAML 식별자)',
								name: 'id',
								type: 'string',
								default: '',
								placeholder: 'ANT',
								description: 'YAML 시나리오에서 사용하는 자산 식별자 (예: ANT, UR, CNC)',
							},
							{
								displayName: 'Asset Name (AAS 등록명)',
								name: 'name',
								type: 'string',
								default: '',
								placeholder: 'ANT_ROBOT',
								description: 'AAS에 등록된 실제 자산 이름 (예: ANT_ROBOT, UR_ROBOT)',
							},
						],
					},
				],
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const scenarioName = this.getNodeParameter('scenarioName', 0) as string;
		const aasFilePath = this.getNodeParameter('aasFilePath', 0) as string;
		const baseUrl = (this.getNodeParameter('baseUrl', 0) as string).replace(/\/$/, '');
		const assetsParam = this.getNodeParameter('assets', 0) as {
			asset?: Array<{ id: string; name: string }>;
		};

		// 자산 맵 구성
		const assetsList = assetsParam?.asset || [];
		const assets: ScenarioContext['assets'] = {};
		for (const a of assetsList) {
			if (a.id && a.name) {
				assets[a.id] = { id: a.id, name: a.name, locked: false };
			}
		}

		// AAS JSON 파일 로드 (선택적)
		let aasData: unknown = null;
		try {
			const resolvedPath = path.resolve(aasFilePath);
			const content = fs.readFileSync(resolvedPath, 'utf8');
			aasData = JSON.parse(content);
		} catch {
			// AAS 파일이 없어도 진행 가능
		}

		// 시나리오 컨텍스트 초기화
		const scenarioContext: ScenarioContext = {
			name: scenarioName,
			baseUrl,
			assets,
			aas: aasData,
			acq: {},
			lock: false,
			var: null,
			loc: null,
			pos: null,
			lastResponse: null,
			stepHistory: [],
		};

		return [[{ json: { scenarioContext } }]];
	}
}
