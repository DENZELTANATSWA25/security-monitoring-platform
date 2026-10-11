"use client";

import { Palette } from "lucide-react";


import { useTheme } from "@/providers/theme-provider";

import { THEMES } from "@/lib/themes";

export default function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-2">
      <Palette
        className="size-4 text-muted-foreground"
        aria-hidden="true"
      />

      <label htmlFor="soc-theme" className="sr-only">
        Application theme
      </label>

      <select
        id="soc-theme"
        value={theme}
        onChange={(event) => {
          const selected = THEMES.find(
            (item) => item.id === event.target.value
          );

          if (selected) {
            setTheme(selected.id);
          }
        }}
        className="
          h-9 rounded-md border border-input
          bg-background px-3 text-sm text-foreground
          focus-visible:outline-2
          focus-visible:outline-offset-2
          focus-visible:outline-ring
        "
      >
        {THEMES.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))}
      </select>
    </div>
  );
}