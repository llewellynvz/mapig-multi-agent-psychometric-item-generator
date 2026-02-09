import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import { Providers } from "@/components/Providers";
import { TopBar } from "@/components/TopBar";
import { DebugLogger } from "@/components/DebugLogger";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

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
      <body className={`min-h-screen ${manrope.variable} ${spaceGrotesk.variable}`}>
        <Providers>
          <DebugLogger />
          <TopBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
