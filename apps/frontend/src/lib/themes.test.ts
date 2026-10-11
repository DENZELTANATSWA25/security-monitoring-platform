import { describe, expect, it } from "vitest";

import {
  DEFAULT_THEME,
  THEMES,
  THEME_STORAGE_KEY,
  isThemeId,
} from "./themes";

describe("Theme definitions", () => {
  it("defines four unique themes", () => {
    expect(THEMES).toHaveLength(4);

    const ids = THEMES.map((theme) => theme.id);

    expect(new Set(ids).size).toBe(ids.length);
  });

  it("uses Dark SOC as the default theme", () => {
    expect(DEFAULT_THEME).toBe("dark-soc");
  });

  it("defines a dedicated storage key", () => {
    expect(THEME_STORAGE_KEY).toBe(
      "security-soc-theme",
    );
  });

  it("accepts every supported theme ID", () => {
    for (const theme of THEMES) {
      expect(isThemeId(theme.id)).toBe(true);
    }
  });

  it("rejects invalid theme IDs", () => {
    expect(isThemeId("unknown-theme")).toBe(false);
    expect(isThemeId("")).toBe(false);
    expect(isThemeId(null)).toBe(false);
    expect(isThemeId(undefined)).toBe(false);
    expect(isThemeId(123)).toBe(false);
  });
});