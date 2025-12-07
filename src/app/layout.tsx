import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/header";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Frameshift - AI-Powered Product Placement",
  description: "Transform your videos with seamless AI-driven product placement using Veo 3.1 and Grok",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="pb-16">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
