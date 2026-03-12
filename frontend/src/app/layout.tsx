import type { Metadata } from "next";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIZH CA - AI-Powered Accounting & Tally Automation",
  description: "Enterprise accounting automation suite for Chartered Accountants",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
        <Toaster
          position="top-right"
          richColors
          closeButton
          toastOptions={{
            style: { fontFamily: "inherit" },
            classNames: {
              error: "border-red-200",
              success: "border-green-200",
            },
          }}
        />
      </body>
    </html>
  );
}
