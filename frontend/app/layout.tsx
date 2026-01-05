import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";
import { CurrencyProvider } from "@/lib/context/currency-context";
import { Navigation } from "@/components/Navigation";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Personal Asset Manager",
  description: "Local-first financial dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <CurrencyProvider>
            <Navigation />
            <main className="container mx-auto p-4">
              {children}
            </main>
            <Toaster position="top-right" richColors />
          </CurrencyProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
