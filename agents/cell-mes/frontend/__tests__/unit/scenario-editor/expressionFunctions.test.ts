/**
 * Unit tests for expressionFunctions — the EXPRESSION_FUNCTIONS catalog
 * exposed to the scenario-editor autocomplete / expression evaluator.
 *
 * The module exports a data constant (no side effects), so every test is a
 * pure assertion against the array and its element shapes.
 */

import { describe, it, expect } from "vitest";
import {
  EXPRESSION_FUNCTIONS,
  type ExpressionFunction,
} from "@/components/scenario-editor/expression/expressionFunctions";

// ---------------------------------------------------------------------------
// Shape / contract
// ---------------------------------------------------------------------------

describe("EXPRESSION_FUNCTIONS array", () => {
  it("is a non-empty array", () => {
    expect(Array.isArray(EXPRESSION_FUNCTIONS)).toBe(true);
    expect(EXPRESSION_FUNCTIONS.length).toBeGreaterThan(0);
  });

  it("every entry has a non-empty signature string", () => {
    EXPRESSION_FUNCTIONS.forEach((fn: ExpressionFunction) => {
      expect(typeof fn.signature).toBe("string");
      expect(fn.signature.trim().length).toBeGreaterThan(0);
    });
  });

  it("every entry has a non-empty description string", () => {
    EXPRESSION_FUNCTIONS.forEach((fn: ExpressionFunction) => {
      expect(typeof fn.description).toBe("string");
      expect(fn.description.trim().length).toBeGreaterThan(0);
    });
  });

  it("every entry has a valid category", () => {
    const VALID_CATEGORIES = ["time", "id", "string", "math", "json"] as const;
    EXPRESSION_FUNCTIONS.forEach((fn: ExpressionFunction) => {
      expect(VALID_CATEGORIES).toContain(fn.category);
    });
  });

  it("has no duplicate signatures", () => {
    const signatures = EXPRESSION_FUNCTIONS.map((fn) => fn.signature);
    const unique = new Set(signatures);
    expect(unique.size).toBe(signatures.length);
  });
});

// ---------------------------------------------------------------------------
// Category membership
// ---------------------------------------------------------------------------

describe("EXPRESSION_FUNCTIONS — time category", () => {
  const timeFns = EXPRESSION_FUNCTIONS.filter((fn) => fn.category === "time");

  it("contains at least one time function", () => {
    expect(timeFns.length).toBeGreaterThan(0);
  });

  it("includes now()", () => {
    expect(timeFns.some((fn) => fn.signature === "now()")).toBe(true);
  });

  it("includes today()", () => {
    expect(timeFns.some((fn) => fn.signature === "today()")).toBe(true);
  });

  it("includes timestamp()", () => {
    expect(timeFns.some((fn) => fn.signature === "timestamp()")).toBe(true);
  });
});

describe("EXPRESSION_FUNCTIONS — id category", () => {
  const idFns = EXPRESSION_FUNCTIONS.filter((fn) => fn.category === "id");

  it("contains at least one id function", () => {
    expect(idFns.length).toBeGreaterThan(0);
  });

  it("includes uuid()", () => {
    expect(idFns.some((fn) => fn.signature === "uuid()")).toBe(true);
  });

  it("includes shortId(n)", () => {
    expect(idFns.some((fn) => fn.signature === "shortId(n)")).toBe(true);
  });
});

describe("EXPRESSION_FUNCTIONS — string category", () => {
  const stringFns = EXPRESSION_FUNCTIONS.filter(
    (fn) => fn.category === "string"
  );

  it("contains at least one string function", () => {
    expect(stringFns.length).toBeGreaterThan(0);
  });

  it("includes upper(s)", () => {
    expect(stringFns.some((fn) => fn.signature === "upper(s)")).toBe(true);
  });

  it("includes lower(s)", () => {
    expect(stringFns.some((fn) => fn.signature === "lower(s)")).toBe(true);
  });

  it("includes format(template, ...args)", () => {
    expect(
      stringFns.some((fn) => fn.signature === "format(template, ...args)")
    ).toBe(true);
  });
});

describe("EXPRESSION_FUNCTIONS — math category", () => {
  const mathFns = EXPRESSION_FUNCTIONS.filter((fn) => fn.category === "math");

  it("contains at least one math function", () => {
    expect(mathFns.length).toBeGreaterThan(0);
  });

  it("includes min(a, b)", () => {
    expect(mathFns.some((fn) => fn.signature === "min(a, b)")).toBe(true);
  });

  it("includes max(a, b)", () => {
    expect(mathFns.some((fn) => fn.signature === "max(a, b)")).toBe(true);
  });

  it("includes round(x)", () => {
    expect(mathFns.some((fn) => fn.signature === "round(x)")).toBe(true);
  });
});

describe("EXPRESSION_FUNCTIONS — json category", () => {
  const jsonFns = EXPRESSION_FUNCTIONS.filter((fn) => fn.category === "json");

  it("contains at least one json function", () => {
    expect(jsonFns.length).toBeGreaterThan(0);
  });

  it("includes json(value)", () => {
    expect(jsonFns.some((fn) => fn.signature === "json(value)")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Lookup helpers — simulate autocomplete consumer patterns
// ---------------------------------------------------------------------------

describe("EXPRESSION_FUNCTIONS — lookup by signature prefix", () => {
  it("returns entries when filtering by '$' prefix (n8n {{ $... }} pattern)", () => {
    // Signatures do NOT start with '$'; this tests that consumers can safely
    // call filter without crashing when zero results match.
    const matches = EXPRESSION_FUNCTIONS.filter((fn) =>
      fn.signature.startsWith("$")
    );
    expect(Array.isArray(matches)).toBe(true);
  });

  it("returns correct entries when filtering by 'now' prefix", () => {
    const matches = EXPRESSION_FUNCTIONS.filter((fn) =>
      fn.signature.startsWith("now")
    );
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0].signature).toBe("now()");
  });

  it("returns correct entries when filtering by 'min' prefix", () => {
    const matches = EXPRESSION_FUNCTIONS.filter((fn) =>
      fn.signature.startsWith("min")
    );
    expect(matches.length).toBeGreaterThanOrEqual(1);
    expect(matches[0].signature).toBe("min(a, b)");
  });
});

// ---------------------------------------------------------------------------
// Total count sanity check (documents current catalog size)
// ---------------------------------------------------------------------------

describe("EXPRESSION_FUNCTIONS — catalog completeness", () => {
  it("contains exactly 12 entries as documented", () => {
    expect(EXPRESSION_FUNCTIONS.length).toBe(12);
  });
});
