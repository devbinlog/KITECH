import { describe, it, expect } from "vitest";
import { formatSeconds, formatDateTime } from "@/hooks/useScheduler";

describe("formatSeconds", () => {
  it('returns "0\uCD08" for 0 seconds', () => {
    expect(formatSeconds(0)).toBe("0\uCD08");
  });

  it('returns "30\uCD08" for 30 seconds', () => {
    expect(formatSeconds(30)).toBe("30\uCD08");
  });

  it('returns "59\uCD08" for 59 seconds', () => {
    expect(formatSeconds(59)).toBe("59\uCD08");
  });

  it('returns "1\uBD84" for 60 seconds', () => {
    expect(formatSeconds(60)).toBe("1\uBD84");
  });

  it('returns "2\uBD84" for 120 seconds', () => {
    expect(formatSeconds(120)).toBe("2\uBD84");
  });

  it('returns "60\uBD84" for 3599 seconds (just under 1 hour)', () => {
    expect(formatSeconds(3599)).toBe("60\uBD84");
  });

  it('returns "1.0\uC2DC\uAC04" for 3600 seconds (exactly 1 hour)', () => {
    expect(formatSeconds(3600)).toBe("1.0\uC2DC\uAC04");
  });

  it('returns "2.0\uC2DC\uAC04" for 7200 seconds (2 hours)', () => {
    expect(formatSeconds(7200)).toBe("2.0\uC2DC\uAC04");
  });

  it('returns "1.5\uC2DC\uAC04" for 5400 seconds (1.5 hours)', () => {
    expect(formatSeconds(5400)).toBe("1.5\uC2DC\uAC04");
  });

  it('returns "1\uCD08" for 0.5 seconds (rounds to nearest)', () => {
    expect(formatSeconds(0.5)).toBe("1\uCD08");
  });
});

describe("formatDateTime", () => {
  it('formats ISO date string to "yyyy-MM-dd HH:mm"', () => {
    // Use a fixed UTC date and check the formatted output
    const isoStr = "2024-06-15T09:30:00Z";
    const result = formatDateTime(isoStr);
    // The format depends on the local timezone of the test runner,
    // but the pattern should always be yyyy-MM-dd HH:mm
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
  });

  it("formats a date-only ISO string correctly", () => {
    const result = formatDateTime("2024-01-01T00:00:00Z");
    expect(result).toMatch(/^2024-01-01 \d{2}:\d{2}$/);
  });

  it("formats a date with non-zero time correctly", () => {
    // Create a date string using a specific local time to avoid TZ issues
    const date = new Date(2024, 5, 15, 14, 30); // June 15, 2024 14:30 local
    const isoStr = date.toISOString();
    const result = formatDateTime(isoStr);
    expect(result).toBe("2024-06-15 14:30");
  });
});
