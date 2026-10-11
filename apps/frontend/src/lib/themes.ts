export const THEMES = [
    {
        id: "dark-soc",
        label: "Dark SOC",
        description: "Professional dark security workspace.",
    },
    {
        id: "midnight-blue",
        label: "Midnight Blue",
        description: "Deep navy operational interface.",
    },
    {
        id: "light-professional",
        label: "Light Professional",
        description: "Clean, bright enterprise workspace.",
    },
    {
        id: "high-contrast",
        label: "High Contrast",
        description: "Enhanced contrast for accessibility.",
    },
] as const;

export type ThemeId = (typeof THEMES)[number]["id"];

export const DEFAULT_THEME: ThemeId = "dark-soc";

export const THEME_STORAGE_KEY = "security-soc-theme";

export function isThemeId(value: unknown): value is ThemeId {
    return THEMES.some((theme) => theme.id === value);
}