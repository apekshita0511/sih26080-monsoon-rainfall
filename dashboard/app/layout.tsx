import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Monsoon Rainfall Post-Processing",
  description:
    "Regime-aware post-processing of GFS monsoon rainfall forecasts over India: real-data verification of raw vs corrected skill (SIH26080, MoES/NCMRWF).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>{children}</body>
    </html>
  );
}
