import React, { createContext, useContext, useEffect, useState } from "react";

type LuminanceMode = "dark" | "light" | "system";
type ColorScheme = "default" | "blue" | "green";

type ThemeProviderProps = {
  children: React.ReactNode;
  defaultTheme?: LuminanceMode;
  defaultColorScheme?: ColorScheme;
  storageKey?: string;
  colorSchemeStorageKey?: string;
};

type ThemeProviderState = {
  theme: LuminanceMode;
  colorScheme: ColorScheme;
  setTheme: (theme: LuminanceMode) => void;
  setColorScheme: (colorScheme: ColorScheme) => void;
};

const initialState: ThemeProviderState = {
  theme: "system",
  colorScheme: "default",
  setTheme: () => null,
  setColorScheme: () => null,
};

const ThemeProviderContext = createContext<ThemeProviderState>(initialState);

export function ThemeProvider({
  children,
  defaultTheme = "system",
  defaultColorScheme = "default",
  storageKey = "vite-ui-theme",
  colorSchemeStorageKey = "vite-ui-color-scheme",
  ...props
}: ThemeProviderProps) {
  const [theme, setThemeState] = useState<LuminanceMode>(
    () => (localStorage.getItem(storageKey) as LuminanceMode) || defaultTheme
  );

  const [colorScheme, setColorSchemeState] = useState<ColorScheme>(
    () => (localStorage.getItem(colorSchemeStorageKey) as ColorScheme) || defaultColorScheme
  );

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.remove("theme-default", "theme-blue", "theme-green");

    // Apply luminance mode
    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }

    // Apply color scheme
    root.classList.add(`theme-${colorScheme}`);
  }, [theme, colorScheme]);

  const value = {
    theme,
    colorScheme,
    setTheme: (newTheme: LuminanceMode) => {
      localStorage.setItem(storageKey, newTheme);
      setThemeState(newTheme);
    },
    setColorScheme: (newColorScheme: ColorScheme) => {
      localStorage.setItem(colorSchemeStorageKey, newColorScheme);
      setColorSchemeState(newColorScheme);
    },
  };

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);
  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider");
  return context;
};
