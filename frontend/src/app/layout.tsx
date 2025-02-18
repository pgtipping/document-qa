import { Providers } from "@/components/Providers";
import { Toaster } from "@/components/ui/toaster";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "./compiled.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Document Q&A",
  description: "Ask questions about your documents using AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body
        className={`${inter.className} ${inter.variable} min-h-screen bg-background text-foreground [&.dark]:bg-background [&.dark]:text-foreground [&.light]:bg-background [&.light]:text-foreground`}
        data-theme="light"
      >
        <Providers>
          <main
            className="min-h-screen bg-background text-foreground [&.dark]:bg-background [&.dark]:text-foreground [&.light]:bg-background [&.light]:text-foreground"
            data-theme="light"
          >
            {children}
          </main>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
