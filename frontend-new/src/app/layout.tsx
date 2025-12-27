import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: "Stock Analytics Pro",
  description: "Institutional Grade Stock Analysis Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className="antialiased bg-background text-foreground min-h-screen font-sans"
      >
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
