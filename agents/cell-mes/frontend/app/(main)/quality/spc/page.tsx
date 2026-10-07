"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { qualityService } from "@/services/quality";
import { SPCData, InspectionPlan, QualityFilters } from "@/types";
import { 
  BarChart3, 
  TrendingUp, 
  RefreshCw, 
  Download,
  AlertTriangle,
  CheckCircle,
  Info
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  AreaChart
} from "recharts";

interface SPCChartProps {
  data: SPCData[];
  title: string;
  type: "xbar" | "r";
}

function SPCChart({ data, title, type }: SPCChartProps) {
  const processedData = data.map((item, index) => ({
    sample: index + 1,
    value: type === "xbar" ? item.x_bar : item.r_value,
    ucl: type === "xbar" ? item.ucl_x : item.ucl_r,
    lcl: type === "xbar" ? item.lcl_x : item.lcl_r,
    date: new Date(item.sample_date).toLocaleDateString(),
  }));

  const isOutOfControl = (value: number, ucl: number, lcl: number) => {
    return value > ucl || value < lcl;
  };

  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    const isOOC = isOutOfControl(payload.value, payload.ucl, payload.lcl);
    
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={isOOC ? "#ef4444" : "#3b82f6"}
        stroke={isOOC ? "#dc2626" : "#2563eb"}
        strokeWidth={2}
      />
    );
  };

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={processedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sample" />
          <YAxis />
          <Tooltip 
            labelFormatter={(label) => `샘플 #${label}`}
            formatter={(value: any, name: string) => {
              const formatValue = (v: any) => typeof v === 'number' ? v.toFixed(3) : v;
              switch(name) {
                case 'value':
                  return [formatValue(value), type === 'xbar' ? 'X̄' : 'R'];
                case 'ucl':
                  return [formatValue(value), 'UCL'];
                case 'lcl':
                  return [formatValue(value), 'LCL'];
                default:
                  return [formatValue(value), name];
              }
            }}
          />
          
          {/* Control Limits */}
          <Area
            dataKey="ucl"
            stroke="#f59e0b"
            fill="none"
            strokeDasharray="5 5"
            strokeWidth={2}
            legendType="none"
          />
          <Area
            dataKey="lcl"
            stroke="#f59e0b"
            fill="none"
            strokeDasharray="5 5"
            strokeWidth={2}
            legendType="none"
          />
          
          {/* Data Line */}
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={<CustomDot />}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function SPCPage() {
  const queryClient = useQueryClient();
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [dateRange, setDateRange] = useState({
    date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0],
  });

  const { data: plans } = useQuery({
    queryKey: ["inspection-plans-for-spc"],
    queryFn: () => qualityService.getInspectionPlans({ limit: 100 }),
  });

  // Derive selected plan's characteristic for the SPC API
  const selectedPlan = plans?.items.find(p => p.id === selectedPlanId);
  const selectedCharacteristic = selectedPlan?.characteristic;

  const { data: spcData, isLoading } = useQuery({
    queryKey: ["spc-data", selectedPlanId, selectedCharacteristic, dateRange],
    queryFn: () => selectedCharacteristic
      ? qualityService.getSPCData(selectedCharacteristic, dateRange.date_from, dateRange.date_to)
      : Promise.resolve([]),
    enabled: !!selectedCharacteristic,
  });

  const generateMutation = useMutation({
    mutationFn: ({ inspection_item_id, sample_size }: { inspection_item_id: number, sample_size: number }) =>
      qualityService.generateSPCData(inspection_item_id, sample_size),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["spc-data"] });
    },
    onError: (error: any) => {
      alert(`SPC 데이터 생성 실패: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Backend InspectionPlan has flat characteristic/usl/lsl fields per plan
  // Also support legacy nested inspection_items if present
  const availableItems = plans?.items.flatMap(plan => {
    if (plan.characteristic) {
      // Backend flat model: each plan IS one characteristic
      return [{
        id: plan.id,
        inspection_plan_id: plan.id,
        item_name: plan.characteristic,
        specification: plan.nominal != null ? `${plan.nominal}` : "-",
        usl: plan.usl ?? null,
        lsl: plan.lsl ?? null,
        target: plan.nominal ?? null,
        measurement_method: plan.inspection_type,
        sort_order: 0,
        product_name: plan.product?.name,
        inspection_type: plan.inspection_type,
      }];
    }
    // Legacy nested model
    return plan.inspection_items?.map(item => ({
      ...item,
      product_name: plan.product?.name,
      inspection_type: plan.inspection_type,
    })) || [];
  }) || [];

  const selectedPlanIdInfo = availableItems.find(item => item.id === selectedPlanId);

  const getControlStatus = (data: SPCData[]) => {
    if (!data.length) return { status: "no-data", message: "데이터 없음", color: "gray" };

    const oocCount = data.filter(p =>
      p.x_bar > p.ucl_x || p.x_bar < p.lcl_x ||
      p.r_value > p.ucl_r || p.r_value < p.lcl_r
    ).length;

    if (oocCount > 0) {
      return { status: "out-of-control", message: `관리 이탈 (${oocCount}건)`, color: "red" };
    }

    return { status: "in-control", message: "관리 상태", color: "green" };
  };

  const controlStatus = getControlStatus(spcData || []);

  const calculateCapabilityIndices = (data: SPCData[]) => {
    if (!data.length || selectedPlanIdInfo?.usl == null || selectedPlanIdInfo?.lsl == null) return null;

    const values = data.flatMap(d => d.sample_values);
    if (values.length < 2) return null;
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return { cp: Infinity, cpk: Infinity, mean, stdDev };

    const usl = selectedPlanIdInfo.usl;
    const lsl = selectedPlanIdInfo.lsl;

    const cp = (usl - lsl) / (6 * stdDev);
    const cpk = Math.min((usl - mean) / (3 * stdDev), (mean - lsl) / (3 * stdDev));

    return { cp, cpk, mean, stdDev };
  };

  const capability = calculateCapabilityIndices(spcData || []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">SPC 관리차트</h1>
        <div className="flex items-center gap-2">
          {selectedPlanId && (
            <>
              <button
                className="btn btn-outline flex items-center gap-2"
                title="SPC 데이터는 검사 결과에서 자동 생성됩니다"
                disabled
              >
                <RefreshCw size={16} />
                데이터 생성
              </button>
              <button className="btn btn-outline flex items-center gap-2">
                <Download size={16} />
                내보내기
              </button>
            </>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">검사항목:</label>
            <select
              value={selectedPlanId || ""}
              onChange={(e) => setSelectedPlanId(e.target.value ? parseInt(e.target.value) : null)}
              className="px-3 py-2 border rounded-md min-w-64"
            >
              <option value="">검사항목을 선택하세요...</option>
              {availableItems.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.product_name} - {item.item_name} ({item.specification})
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">기간:</label>
            <input
              type="date"
              value={dateRange.date_from}
              onChange={(e) => setDateRange({ ...dateRange, date_from: e.target.value })}
              className="px-3 py-1 border rounded text-sm"
            />
            <span className="text-gray-500">~</span>
            <input
              type="date"
              value={dateRange.date_to}
              onChange={(e) => setDateRange({ ...dateRange, date_to: e.target.value })}
              className="px-3 py-1 border rounded text-sm"
            />
          </div>
        </div>
      </div>

      {selectedPlanId ? (
        <>
          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">관리상태</p>
                  <p className={`text-lg font-bold ${
                    controlStatus.color === "green" ? "text-green-600" : 
                    controlStatus.color === "red" ? "text-red-600" : "text-gray-600"
                  }`}>
                    {controlStatus.message}
                  </p>
                </div>
                <div className={`p-3 rounded-full ${
                  controlStatus.color === "green" ? "bg-green-100" : 
                  controlStatus.color === "red" ? "bg-red-100" : "bg-gray-100"
                }`}>
                  {controlStatus.status === "in-control" ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : controlStatus.status === "out-of-control" ? (
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  ) : (
                    <Info className="h-6 w-6 text-gray-600" />
                  )}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">샘플 수</p>
                  <p className="text-lg font-bold text-primary-600">{spcData?.length || 0}</p>
                </div>
                <div className="p-3 rounded-full bg-primary-100">
                  <BarChart3 className="h-6 w-6 text-primary-600" />
                </div>
              </div>
            </div>

            {capability && (
              <>
                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Cp (공정능력)</p>
                      <p className={`text-lg font-bold ${capability.cp >= 1.33 ? "text-green-600" : capability.cp >= 1.0 ? "text-yellow-600" : "text-red-600"}`}>
                        {isFinite(capability.cp) ? (capability.cp ?? 0).toFixed(2) : "∞"}
                      </p>
                    </div>
                    <div className={`p-3 rounded-full ${capability.cp >= 1.33 ? "bg-green-100" : capability.cp >= 1.0 ? "bg-yellow-100" : "bg-red-100"}`}>
                      <TrendingUp className={`h-6 w-6 ${capability.cp >= 1.33 ? "text-green-600" : capability.cp >= 1.0 ? "text-yellow-600" : "text-red-600"}`} />
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-600">Cpk (공정성능)</p>
                      <p className={`text-lg font-bold ${capability.cpk >= 1.33 ? "text-green-600" : capability.cpk >= 1.0 ? "text-yellow-600" : "text-red-600"}`}>
                        {isFinite(capability.cpk) ? (capability.cpk ?? 0).toFixed(2) : "∞"}
                      </p>
                      {capability.cpk < 0 && (
                        <p className="text-xs text-red-700 font-medium mt-1">공정 중심이 규격 밖</p>
                      )}
                    </div>
                    <div className={`p-3 rounded-full ${capability.cpk >= 1.33 ? "bg-green-100" : capability.cpk >= 1.0 ? "bg-yellow-100" : "bg-red-100"}`}>
                      <TrendingUp className={`h-6 w-6 ${capability.cpk >= 1.33 ? "text-green-600" : capability.cpk >= 1.0 ? "text-yellow-600" : "text-red-600"}`} />
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Item Info */}
          {selectedPlanIdInfo && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">검사항목 정보</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="text-sm text-gray-600">제품명</label>
                  <p className="font-medium">{selectedPlanIdInfo.product_name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">검사항목</label>
                  <p className="font-medium">{selectedPlanIdInfo.item_name}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">규격</label>
                  <p className="font-medium">{selectedPlanIdInfo.specification}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">측정방법</label>
                  <p className="font-medium">{selectedPlanIdInfo.measurement_method}</p>
                </div>
              </div>
            </div>
          )}

          {/* Charts */}
          {isLoading ? (
            <div className="text-center py-8 text-gray-500">차트 로딩 중...</div>
          ) : spcData && spcData.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* X-bar Chart */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">X̄ 관리차트 (평균)</h2>
                  <BarChart3 className="h-5 w-5 text-gray-400" />
                </div>
                <SPCChart data={spcData} title="X-bar Chart" type="xbar" />
                
                {/* X-bar Statistics */}
                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <p className="text-gray-600">UCL</p>
                    <p className="font-medium">{(spcData[0]?.ucl_x ?? 0).toFixed(3)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600">평균</p>
                    <p className="font-medium">
                      {spcData.length > 0 
                        ? (spcData.reduce((sum, d) => sum + d.x_bar, 0) / spcData.length).toFixed(3)
                        : "0"
                      }
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600">LCL</p>
                    <p className="font-medium">{(spcData[0]?.lcl_x ?? 0).toFixed(3)}</p>
                  </div>
                </div>
              </div>

              {/* R Chart */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">R 관리차트 (범위)</h2>
                  <BarChart3 className="h-5 w-5 text-gray-400" />
                </div>
                <SPCChart data={spcData} title="R Chart" type="r" />
                
                {/* R Statistics */}
                <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <p className="text-gray-600">UCL</p>
                    <p className="font-medium">{(spcData[0]?.ucl_r ?? 0).toFixed(3)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600">평균</p>
                    <p className="font-medium">
                      {spcData.length > 0 
                        ? (spcData.reduce((sum, d) => sum + d.r_value, 0) / spcData.length).toFixed(3)
                        : "0"
                      }
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-gray-600">LCL</p>
                    <p className="font-medium">{(spcData[0]?.lcl_r ?? 0).toFixed(3)}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
              <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500 mb-4">SPC 데이터가 없습니다.</p>
              <p className="text-sm text-gray-400">검사결과를 등록하면 SPC 데이터가 자동으로 생성됩니다.</p>
            </div>
          )}

          {/* Analysis Notes */}
          {capability && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">분석 결과</h3>
              <div className="space-y-3">
                <div className="p-3 bg-primary-50 rounded-lg">
                  <h4 className="font-medium text-primary-900 mb-1">공정 능력 해석</h4>
                  <ul className="text-sm text-primary-800 space-y-1">
                    <li>• Cp ≥ 1.33: 우수한 공정능력</li>
                    <li>• 1.00 ≤ Cp &lt; 1.33: 적절한 공정능력</li>
                    <li>• Cp &lt; 1.00: 개선이 필요한 공정능력</li>
                  </ul>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">현재 통계값</h4>
                    <div className="text-sm space-y-1">
                      <p>평균: {(capability.mean ?? 0).toFixed(3)}</p>
                      <p>표준편차: {(capability.stdDev ?? 0).toFixed(3)}</p>
                      <p>상한선: {selectedPlanIdInfo?.usl}</p>
                      <p>하한선: {selectedPlanIdInfo?.lsl}</p>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <h4 className="font-medium mb-2">개선 제안</h4>
                    <div className="text-sm space-y-1">
                      {isFinite(capability.cp) && capability.cp < 1.0 && <p>• 공정 변동 감소 필요</p>}
                      {isFinite(capability.cpk) && capability.cpk < 1.0 && <p>• 공정 중심 조정 필요</p>}
                      {controlStatus.status === "out-of-control" && <p>• 특별 원인 조사 필요</p>}
                      {capability.cp >= 1.33 && capability.cpk >= 1.33 && <p>• 우수한 공정 상태 유지</p>}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-gray-500 mb-4">분석할 검사항목을 선택해주세요.</p>
          <p className="text-sm text-gray-400">검사계획에서 등록된 검사항목들을 확인하실 수 있습니다.</p>
        </div>
      )}
    </div>
  );
}