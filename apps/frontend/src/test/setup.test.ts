import { describe, expect, it } from "vitest";

describe("Frontend testing infrastructure", () => {
  it("runs Vitest successfully", () => {
    expect(2 + 2).toBe(4);
  });

  it("provides a browser-like environment", () => {
    expect(document).toBeDefined();
    expect(window).toBeDefined();
  });
});