import {
  beforeEach,
  describe,
  expect,
  it,
} from "vitest";

import {
  act,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";

import {
  ThemeProvider,
  useTheme,
} from "./theme-provider";

import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
} from "@/lib/themes";

function ThemeConsumer() {
  const { theme, setTheme } = useTheme();

  return (
    <div>
      <p data-testid="current-theme">{theme}</p>

      <button
        type="button"
        onClick={() => setTheme("midnight-blue")}
      >
        Select Midnight Blue
      </button>

      <button
        type="button"
        onClick={() => setTheme("high-contrast")}
      >
        Select High Contrast
      </button>
    </div>
  );
}

function renderProvider() {
  return render(
    <ThemeProvider>
      <ThemeConsumer />
    </ThemeProvider>,
  );
}

describe("ThemeProvider", () => {
  beforeEach(() => {
    localStorage.clear();

    delete document.documentElement.dataset.theme;
  });

  it("uses the default theme when no preference exists", () => {
    renderProvider();

    expect(
      screen.getByTestId("current-theme"),
    ).toHaveTextContent(DEFAULT_THEME);
  });

  it("restores a valid saved theme", () => {
    localStorage.setItem(
      THEME_STORAGE_KEY,
      "midnight-blue",
    );

    renderProvider();

    expect(
      screen.getByTestId("current-theme"),
    ).toHaveTextContent("midnight-blue");
  });

  it("falls back to the default for an invalid saved theme", () => {
    localStorage.setItem(
      THEME_STORAGE_KEY,
      "invalid-theme",
    );

    renderProvider();

    expect(
      screen.getByTestId("current-theme"),
    ).toHaveTextContent(DEFAULT_THEME);
  });

  it("persists theme changes to localStorage", () => {
    renderProvider();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Select Midnight Blue",
      }),
    );

    expect(
      localStorage.getItem(THEME_STORAGE_KEY),
    ).toBe("midnight-blue");
  });

  it("applies the selected theme to the document", () => {
    renderProvider();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Select High Contrast",
      }),
    );

    expect(
      document.documentElement.dataset.theme,
    ).toBe("high-contrast");
  });

  it("updates subscribers when the theme changes", () => {
    renderProvider();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Select Midnight Blue",
      }),
    );

    expect(
      screen.getByTestId("current-theme"),
    ).toHaveTextContent("midnight-blue");
  });

  it("responds to storage changes from another tab", () => {
    renderProvider();

    act(() => {
      localStorage.setItem(
        THEME_STORAGE_KEY,
        "high-contrast",
      );

      window.dispatchEvent(new Event("storage"));
    });

    expect(
      screen.getByTestId("current-theme"),
    ).toHaveTextContent("high-contrast");
  });
});