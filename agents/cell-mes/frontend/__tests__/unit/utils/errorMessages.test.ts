import { describe, it, expect } from "vitest";
import {
  getErrorMessage,
  getQualityErrorMessage,
  getSuccessMessage,
  getConfirmMessage,
  ErrorInfo,
} from "@/utils/errorMessages";

describe("getErrorMessage", () => {
  it("returns network error message for ERR_NETWORK code", () => {
    const error: ErrorInfo = { code: "ERR_NETWORK" };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC11C\uBC84\uC5D0 \uC5F0\uACB0\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4");
  });

  it("returns 401 message for unauthorized errors", () => {
    const error: ErrorInfo = { response: { status: 401 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uB85C\uADF8\uC778\uC774 \uD544\uC694\uD569\uB2C8\uB2E4");
  });

  it("returns 404 message for not found errors", () => {
    const error: ErrorInfo = { response: { status: 404 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uCC3E\uC744 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4");
  });

  it('returns product not found message for 400 with "Product not found"', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "Product not found in database" } },
    };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC81C\uD488\uC774 \uC874\uC7AC\uD558\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4");
  });

  it('returns duplicate message for 400 with "already exists"', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "Record already exists" } },
    };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC774\uBBF8 \uC874\uC7AC\uD558\uB294 \uB370\uC774\uD130");
  });

  it('returns duplicate message for 400 with "duplicate"', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "duplicate key error" } },
    };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC774\uBBF8 \uC874\uC7AC\uD558\uB294 \uB370\uC774\uD130");
  });

  it('returns routing message for 400 with "routing"', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "routing not configured" } },
    };
    const result = getErrorMessage(error);
    expect(result).toContain("\uB77C\uC6B0\uD305");
  });

  it("returns generic 400 message when no specific detail matches", () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "something else" } },
    };
    const result = getErrorMessage(error);
    expect(result).toContain("something else");
  });

  it("returns default 400 message when detail is absent", () => {
    const error: ErrorInfo = { response: { status: 400 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC785\uB825 \uB370\uC774\uD130\uB97C \uD655\uC778\uD574\uC8FC\uC138\uC694");
  });

  it("returns 500 server error message", () => {
    const error: ErrorInfo = { response: { status: 500 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC11C\uBC84 \uC624\uB958");
  });

  it("returns 403 forbidden message", () => {
    const error: ErrorInfo = { response: { status: 403 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uAD8C\uD55C\uC774 \uC5C6\uC2B5\uB2C8\uB2E4");
  });

  it("returns 422 validation error message", () => {
    const error: ErrorInfo = { response: { status: 422 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uD544\uC218 \uD56D\uBAA9\uC774 \uB204\uB77D");
  });

  it("uses custom context prefix", () => {
    const error: ErrorInfo = { response: { status: 500 } };
    const result = getErrorMessage(error, "\uC8FC\uBB38 \uC800\uC7A5");
    expect(result).toMatch(/^\uC8FC\uBB38 \uC800\uC7A5 \uC2E4\uD328:/);
  });

  it("falls back to error.message for unknown status codes", () => {
    const error: ErrorInfo = {
      response: { status: 418 },
      message: "I'm a teapot",
    };
    const result = getErrorMessage(error);
    expect(result).toContain("I'm a teapot");
  });

  it('falls back to generic message when no error.message and unknown status', () => {
    const error: ErrorInfo = { response: { status: 418 } };
    const result = getErrorMessage(error);
    expect(result).toContain("\uC54C \uC218 \uC5C6\uB294 \uC624\uB958");
  });

  it("uses default context when none provided", () => {
    const error: ErrorInfo = { response: { status: 401 } };
    const result = getErrorMessage(error);
    expect(result).toMatch(/^\uC791\uC5C5 \uC2E4\uD328:/);
  });
});

describe("getQualityErrorMessage", () => {
  it('uses "\uAC80\uC0AC\uACC4\uD68D" context for inspection_plan errors', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "inspection_plan not found" } },
    };
    const result = getQualityErrorMessage(error);
    expect(result).toMatch(/^\uAC80\uC0AC\uACC4\uD68D \uC2E4\uD328:/);
  });

  it('uses "\uAC80\uC0AC\uACB0\uACFC" context for inspection_result errors', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "inspection_result invalid" } },
    };
    const result = getQualityErrorMessage(error);
    expect(result).toMatch(/^\uAC80\uC0AC\uACB0\uACFC \uC2E4\uD328:/);
  });

  it('uses "\uBD80\uC801\uD569\uBCF4\uACE0\uC11C" context for ncr errors', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "ncr creation failed" } },
    };
    const result = getQualityErrorMessage(error);
    expect(result).toMatch(/^\uBD80\uC801\uD569\uBCF4\uACE0\uC11C \uC2E4\uD328:/);
  });

  it('uses "SPC \uCC28\uD2B8" context for spc errors', () => {
    const error: ErrorInfo = {
      response: { status: 400, data: { detail: "spc data error" } },
    };
    const result = getQualityErrorMessage(error);
    expect(result).toMatch(/^SPC \uCC28\uD2B8 \uC2E4\uD328:/);
  });

  it('falls back to "\uD488\uC9C8 \uAD00\uB9AC" context for unmatched errors', () => {
    const error: ErrorInfo = {
      response: { status: 500 },
    };
    const result = getQualityErrorMessage(error);
    expect(result).toMatch(/^\uD488\uC9C8 \uAD00\uB9AC \uC2E4\uD328:/);
  });
});

describe("getSuccessMessage", () => {
  it("returns count-based message when count is provided", () => {
    const result = getSuccessMessage("\uC0AD\uC81C", 3);
    expect(result).toBe("\uC0AD\uC81C \uC644\uB8CC: 3\uAC74\uC774 \uCC98\uB9AC\uB418\uC5C8\uC2B5\uB2C8\uB2E4.");
  });

  it("returns count-based message with count of 0", () => {
    const result = getSuccessMessage("\uC0AD\uC81C", 0);
    expect(result).toBe("\uC0AD\uC81C \uC644\uB8CC: 0\uAC74\uC774 \uCC98\uB9AC\uB418\uC5C8\uC2B5\uB2C8\uB2E4.");
  });

  it("returns simple completion message when count is not provided", () => {
    const result = getSuccessMessage("\uC800\uC7A5");
    expect(result).toBe("\uC800\uC7A5\uC774(\uAC00) \uC644\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4.");
  });
});

describe("getConfirmMessage", () => {
  it("includes target text when target is provided", () => {
    const result = getConfirmMessage("\uC0AD\uC81C", "\uC8FC\uBB38 #123");
    expect(result).toContain("\uC8FC\uBB38 #123");
    expect(result).toContain("\uC0AD\uC81C");
  });

  it("includes only action when target is not provided", () => {
    const result = getConfirmMessage("\uC0AD\uC81C");
    expect(result).toContain("\uC0AD\uC81C");
    expect(result).toMatch(/^\uC815\uB9D0\uB85C\s+\uC0AD\uC81C\uD558\uC2DC\uACA0\uC2B5\uB2C8\uAE4C\?$/);
  });

  it("wraps target in quotes", () => {
    const result = getConfirmMessage("\uC218\uC815", "\uC124\uBE44 A");
    expect(result).toContain('"\uC124\uBE44 A"');
  });
});
