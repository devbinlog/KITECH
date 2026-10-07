"use client";

/**
 * KitechLogo — KITECH 한국생산기술연구원 공식 로고 아이콘.
 *
 * 원본 이미지: https://www.kitech.re.kr/images/common/logo.png (255x72, RGBA)
 * 좌측 32% 크롭 + 정사각형 패딩 처리 후 public/kitech-logo-square.png 저장.
 *
 * 투명 배경 PNG라 어두운 sidebar 배경에서도 자연스럽게 표시.
 *
 * Defaults to 36px square. Pass `size` prop to scale.
 */
interface KitechLogoProps {
  /** Pixel size (square). Default 36. */
  size?: number;
  /** Optional className appended to the <img>. */
  className?: string;
  /** ARIA label. Default "KITECH". */
  ariaLabel?: string;
}

export function KitechLogo({
  size = 36,
  className = "",
  ariaLabel = "KITECH 한국생산기술연구원",
}: KitechLogoProps) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/kitech-logo-square.png"
      alt={ariaLabel}
      width={size}
      height={size}
      className={className}
      style={{ width: size, height: size, objectFit: "contain" }}
    />
  );
}
