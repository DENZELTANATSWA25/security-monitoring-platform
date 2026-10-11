import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";

import QueryProvider from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Security SOC",
    template: "%s | Security SOC",
  },
  description:
    "AI-powered threat detection and security monitoring platform.",
};

const themeInitializationScript = `
(function () {
  try {
    var stored = localStorage.getItem("security-soc-theme");
    var allowed = [
      "dark-soc",
      "midnight-blue",
      "light-professional",
      "high-contrast"
    ];

    var theme = allowed.includes(stored)
      ? stored
      : "dark-soc";

    document.documentElement.dataset.theme = theme;
  } catch (_) {
    document.documentElement.dataset.theme = "dark-soc";
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
        <head>
            <script
                dangerouslySetInnerHTML={{
                    __html: themeInitializationScript,
                }}
            />
        </head>

      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <QueryProvider>
            <ThemeProvider>{children}</ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}