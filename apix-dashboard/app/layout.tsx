import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "APIx — India Airfare Price Index",
  description:
    "A daily measure of domestic airfare movement across India's major passenger routes for MoSPI CPI augmentation (SIH Problem Statement SIH-26056).",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className="min-h-full flex flex-col bg-[#F4F2EC] text-[#111716] antialiased" suppressHydrationWarning>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
