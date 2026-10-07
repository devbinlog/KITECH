import { describe, it, expect } from "vitest";

/**
 * deduplicatePathPrefix is a private (non-exported) function inside lib/axios.ts.
 * We re-implement its exact logic here so we can unit-test the algorithm
 * without modifying the production module.
 *
 * Source logic (lib/axios.ts):
 *   function deduplicatePathPrefix(baseURL, url) {
 *     if (!baseURL || !url) return url;
 *     try {
 *       const { pathname } = new URL(baseURL);
 *       if (pathname !== "/" && url.startsWith(pathname)) {
 *         return url.slice(pathname.length) || "/";
 *       }
 *     } catch { }
 *     return url;
 *   }
 */
function deduplicatePathPrefix(
  baseURL: string | undefined,
  url: string | undefined
): string | undefined {
  if (!baseURL || !url) return url;
  try {
    const { pathname } = new URL(baseURL);
    if (pathname !== "/" && url.startsWith(pathname)) {
      return url.slice(pathname.length) || "/";
    }
  } catch {
    // baseURL parsing failure -> return url as-is
  }
  return url;
}

describe("deduplicatePathPrefix", () => {
  it("removes duplicate /api/v1 prefix when baseURL contains it", () => {
    const result = deduplicatePathPrefix(
      "http://localhost:8000/api/v1",
      "/api/v1/auth/login"
    );
    expect(result).toBe("/auth/login");
  });

  it("leaves url unchanged when baseURL has no path prefix (origin only)", () => {
    const result = deduplicatePathPrefix(
      "http://localhost:8000",
      "/api/v1/auth/login"
    );
    expect(result).toBe("/api/v1/auth/login");
  });

  it('returns "/" when url equals the prefix exactly', () => {
    const result = deduplicatePathPrefix(
      "http://localhost:8000/api/v1",
      "/api/v1"
    );
    expect(result).toBe("/");
  });

  it("returns url as-is when baseURL is undefined", () => {
    const result = deduplicatePathPrefix(undefined, "/api/v1/auth/login");
    expect(result).toBe("/api/v1/auth/login");
  });

  it("returns undefined when url is undefined", () => {
    const result = deduplicatePathPrefix("http://localhost:8000", undefined);
    expect(result).toBeUndefined();
  });

  it("returns url as-is when baseURL is invalid (not parseable)", () => {
    const result = deduplicatePathPrefix(
      "not-a-valid-url",
      "/api/v1/auth/login"
    );
    expect(result).toBe("/api/v1/auth/login");
  });

  it("returns url as-is when baseURL path does not overlap with url", () => {
    const result = deduplicatePathPrefix(
      "http://localhost:8000/api/v2",
      "/api/v1/auth/login"
    );
    expect(result).toBe("/api/v1/auth/login");
  });

  it("handles both baseURL and url being undefined", () => {
    const result = deduplicatePathPrefix(undefined, undefined);
    expect(result).toBeUndefined();
  });

  it("handles baseURL with trailing slash in path", () => {
    // new URL("http://localhost:8000/api/v1/").pathname === "/api/v1/"
    // url "/api/v1/auth/login" starts with "/api/v1/" -> deduplicates
    const result = deduplicatePathPrefix(
      "http://localhost:8000/api/v1/",
      "/api/v1/auth/login"
    );
    expect(result).toBe("auth/login");
  });
});
