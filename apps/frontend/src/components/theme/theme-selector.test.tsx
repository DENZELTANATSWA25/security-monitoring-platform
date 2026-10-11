import {
  beforeEach,
  describe,
  expect,
  it,
} from "vitest";

import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import ThemeSelector from "./theme-selector";

import {
  ThemeProvider,
} from "@/providers/theme-provider";

import {
  DEFAULT_THEME,
  THEMES,
  THEME_STORAGE_KEY,
} from "@/lib/themes";

function renderSelector() {
  return render(
    <ThemeProvider>
      <ThemeSelector />
    </ThemeProvider>,
  );
}

describe("ThemeSelector", () => {
  beforeEach(() => {
    localStorage.clear();

    delete document.documentElement.dataset.theme;
  });

  it("displays every available theme", () => {
    renderSelector();

    const selector = screen.getByRole("combobox", {
      name: "Application theme",
    });

    expect(
      selector.querySelectorAll("option"),
    ).toHaveLength(THEMES.length);

    for (const theme of THEMES) {
      expect(
        screen.getByRole("option", {
          name: theme.label,
        }),
      ).toBeInTheDocument();
    }
  });

  it("selects the default theme initially", () => {
    renderSelector();

    expect(
      screen.getByRole("combobox", {
        name: "Application theme",
      }),
    ).toHaveValue(DEFAULT_THEME);
  });

  it("displays the saved theme selection", () => {
    localStorage.setItem(
      THEME_STORAGE_KEY,
      "light-professional",
    );

    renderSelector();

    expect(
      screen.getByRole("combobox", {
        name: "Application theme",
      }),
    ).toHaveValue("light-professional");
  });

  it("allows switching to Midnight Blue", () => {
    renderSelector();

    fireEvent.change(
      screen.getByRole("combobox", {
        name: "Application theme",
      }),
      {
        target: {
          value: "midnight-blue",
        },
      },
    );

    expect(
      localStorage.getItem(THEME_STORAGE_KEY),
    ).toBe("midnight-blue");

    expect(
      document.documentElement.dataset.theme,
    ).toBe("midnight-blue");
  });

  it("allows switching to High Contrast", () => {
    renderSelector();

    fireEvent.change(
      screen.getByRole("combobox", {
        name: "Application theme",
      }),
      {
        target: {
          value: "high-contrast",
        },
      },
    );

    expect(
      screen.getByRole("combobox", {
        name: "Application theme",
      }),
    ).toHaveValue("high-contrast");
  });
});