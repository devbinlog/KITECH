import type { Config } from "tailwindcss";

/**
 * Tailwind theme — KITECH brand palette.
 *
 * Brand reference:
 *   - KITECH BLUE  CMYK 95.73.0.0  / Pantone 2728C / DIC 2601 ≈ #0047BB
 *   - KITECH GREEN CMYK 55.0.100.0 / Pantone 376C  / DIC 642  ≈ #84BD00
 *   - KITECH GRAY  CMYK 0.15.0.55  (별도 제작)               ≈ #857C82
 *
 * Mapping:
 *   - primary  ← KITECH BLUE  (메인 액션 / 링크 / 활성 상태)
 *   - secondary ← KITECH GREEN (서브 액션 / 강조 / 배지)
 *   - neutral  ← KITECH GRAY  (텍스트 / 보더 / 비활성)
 */
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // KITECH BLUE — Pantone 2728C (#0047BB)
        primary: {
          50: "#EBF1FB",
          100: "#C8D9F4",
          200: "#93B3E9",
          300: "#5E8DDD",
          400: "#2967D2",
          500: "#0047BB",
          600: "#003D9F",
          700: "#003383",
          800: "#002967",
          900: "#001F4B",
          DEFAULT: "#0047BB",
        },
        // KITECH GREEN — Pantone 376C (#84BD00)
        secondary: {
          50: "#F4FAE6",
          100: "#DEF1B0",
          200: "#C0E573",
          300: "#A2D936",
          400: "#93CB1A",
          500: "#84BD00",
          600: "#6FA000",
          700: "#5A8200",
          800: "#466500",
          900: "#324800",
          DEFAULT: "#84BD00",
        },
        // KITECH GRAY — warm gray (#857C82)
        neutral: {
          50: "#F5F3F4",
          100: "#E1DDDF",
          200: "#C7C0C4",
          300: "#ADA3A8",
          400: "#968B91",
          500: "#857C82",
          600: "#6E676C",
          700: "#575256",
          800: "#403D40",
          900: "#2A2729",
          DEFAULT: "#857C82",
        },
        // Status colors (intent-based — kept Tailwind defaults)
        success: "#22c55e",
        warning: "#f59e0b",
        error: "#ef4444",
      },
    },
  },
  plugins: [],
};

export default config;
