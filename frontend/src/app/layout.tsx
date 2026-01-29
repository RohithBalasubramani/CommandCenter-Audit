import type { Metadata } from "next";
import localFont from "next/font/local";
import DevConsoleInterceptor from "@/components/DevConsoleInterceptor";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Command Center — NeuractOS",
  description:
    "The agentic landing page for NeuractOS. One-and-all industrial operations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <DevConsoleInterceptor />
        {children}
      </body>
    </html>
  );
}
