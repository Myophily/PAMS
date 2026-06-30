import type { Metadata } from "next";
import { Toaster } from "sonner";

import { Navigation } from "@/components/Navigation";
import { CurrencyProvider } from "@/lib/context/currency-context";
import { QueryProvider } from "@/lib/query-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Personal Asset Management System",
  description: "Local-first financial dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-[var(--canvas)] text-[var(--ink)] antialiased">
        <QueryProvider>
          <CurrencyProvider>
            <Navigation />
            <main className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
              {children}
            </main>
            <Toaster
              position="top-right"
              toastOptions={{
                classNames: {
                  toast:
                    "border border-[var(--hairline-strong)] bg-[var(--surface-card)] text-[var(--ink)]",
                  description: "text-[var(--charcoal)]",
                  actionButton:
                    "bg-[var(--primary)] text-[var(--primary-on)]",
                  cancelButton:
                    "bg-[var(--surface-elevated)] text-[var(--ink)]",
                },
              }}
            />
          </CurrencyProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
