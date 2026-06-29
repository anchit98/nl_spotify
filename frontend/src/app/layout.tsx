import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { InsightsDataProvider } from "@/components/InsightsDataProvider";
import { Sidebar } from "@/components/Sidebar";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Music Discovery Insights",
  description: "Evidence from public user feedback across app stores, Reddit, forums, and social media.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.variable} antialiased`} suppressHydrationWarning>
        <InsightsDataProvider>
          <Sidebar />
          <main className="flex-1 md:ml-64 min-h-screen pt-16 md:pt-0">{children}</main>
        </InsightsDataProvider>
      </body>
    </html>
  );
}
