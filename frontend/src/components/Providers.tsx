"use client";

import * as React from "react";
import { ThemeProvider } from "next-themes";

export function Providers({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    const updateThemeClass = (theme: string) => {
      const body = document.body;
      const main = document.querySelector("main");

      if (body) {
        body.classList.remove("light", "dark");
        body.classList.add(theme);
        body.style.colorScheme = theme;
        body.dataset.theme = theme;
      }

      if (main) {
        main.classList.remove("light", "dark");
        main.classList.add(theme);
        (main as HTMLElement).style.colorScheme = theme;
        main.dataset.theme = theme;
      }
    };

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (
          mutation.attributeName === "class" &&
          mutation.target instanceof HTMLElement
        ) {
          const htmlTheme = document.documentElement.classList.contains("dark")
            ? "dark"
            : "light";
          updateThemeClass(htmlTheme);
        }
      });
    });

    observer.observe(document.documentElement, { attributes: true });

    return () => observer.disconnect();
  }, [mounted]);

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="light"
      value={{
        dark: "dark",
        light: "light",
      }}
      enableSystem={false}
    >
      {children}
    </ThemeProvider>
  );
}
