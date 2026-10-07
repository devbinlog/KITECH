/**
 * MES UI에서 사용할 사용자 친화적 에러 메시지 처리
 * MES UX Patterns 스킬을 따름
 */

export interface ErrorResponse {
  status?: number;
  data?: {
    detail?: string;
  };
}

export interface ErrorInfo {
  code?: string;
  response?: ErrorResponse;
  message?: string;
}

export function getErrorMessage(error: ErrorInfo, context: string = "작업"): string {
  let message = `${context} 실패: `;

  // Network Error
  if (error.code === "ERR_NETWORK") {
    return message + "서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.";
  }

  const status = error.response?.status;
  const detail = error.response?.data?.detail;

  switch (status) {
    case 400:
      if (detail?.includes("Product not found")) {
        return message + "선택한 제품이 존재하지 않습니다.";
      } else if (detail?.includes("duplicate") || detail?.includes("exists")) {
        return message + "이미 존재하는 데이터입니다.";
      } else if (detail?.includes("routing")) {
        return message + "선택한 제품에 라우팅이 설정되지 않았습니다.";
      } else {
        return message + (detail || "입력 데이터를 확인해주세요.");
      }

    case 401:
      return message + "로그인이 필요합니다.";

    case 403:
      return message + "이 작업에 대한 권한이 없습니다.";

    case 404:
      return message + "요청한 데이터를 찾을 수 없습니다.";

    case 422:
      return message + "필수 항목이 누락되었거나 잘못되었습니다.";

    case 500:
      return message + "서버 오류가 발생했습니다. 관리자에게 문의해주세요.";

    default:
      return message + (error.message || "알 수 없는 오류가 발생했습니다.");
  }
}

/**
 * Quality 관련 특화 에러 메시지
 */
export function getQualityErrorMessage(error: ErrorInfo): string {
  const detail = error.response?.data?.detail;

  if (detail?.includes("inspection_plan")) {
    return getErrorMessage(error, "검사계획");
  } else if (detail?.includes("inspection_result")) {
    return getErrorMessage(error, "검사결과");
  } else if (detail?.includes("ncr")) {
    return getErrorMessage(error, "부적합보고서");
  } else if (detail?.includes("spc")) {
    return getErrorMessage(error, "SPC 차트");
  }

  return getErrorMessage(error, "품질 관리");
}

/**
 * 성공 메시지 생성
 */
export function getSuccessMessage(action: string, count?: number): string {
  if (count !== undefined) {
    return `${action} 완료: ${count}건이 처리되었습니다.`;
  }
  return `${action}이(가) 완료되었습니다.`;
}

/**
 * 확인 메시지 생성
 */
export function getConfirmMessage(action: string, target?: string): string {
  const targetText = target ? ` "${target}"을(를)` : "";
  return `정말로${targetText} ${action}하시겠습니까?`;
}