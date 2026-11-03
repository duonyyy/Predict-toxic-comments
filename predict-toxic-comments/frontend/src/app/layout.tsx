import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "StreamGuard AI - Giám sát Bình luận Độc hại Real-time",
  description: "Hệ thống AI phát hiện và phân tích bình luận độc hại YouTube Live thời gian thực sử dụng ViSoBERT.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#090a0f] text-gray-100 min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
