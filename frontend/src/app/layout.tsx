import type { Metadata } from "next";
import { Providers } from "@/components/Providers";
import { TopBar } from "@/components/TopBar";
import { DebugLogger } from "@/components/DebugLogger";
import "./globals.css";

export const metadata: Metadata = {
  title: "MAPIG – Multi-Agent Psychometric Item Generator",
  description: "Evidence-bounded, multi-agent item drafting for psychometric scale development",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen">
        <Providers>
          <DebugLogger />
          <TopBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
