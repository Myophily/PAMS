"use client";

import { Suspense } from "react";
import { Plus } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { useAccounts } from "@/lib/hooks/useAccounts";
import { AccountCard } from "./_components/AccountCard";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { AddAccountModal } from "@/components/modals/AddAccountModal";
import { AddTransactionModal } from "@/components/modals/AddTransactionModal";
import { TransferModal } from "@/components/modals/TransferModal";
import { ExchangeModal } from "@/components/modals/ExchangeModal";
import { BuySellModal } from "@/components/modals/BuySellModal";
import { DeleteAccountModal } from "@/components/modals/DeleteAccountModal";

function AccountsContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data, isLoading, error } = useAccounts();

  const modal = searchParams.get("modal");
  const accountId = searchParams.get("accountId");

  const handleAddAccount = () => {
    router.push("?modal=add-account");
  };

  const closeModal = () => {
    router.push(pathname);
  };

  // Find the account for delete modal
  const accountToDelete = (data?.accounts || []).find(
    (acc) => acc.id === parseInt(accountId || "0")
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] px-4 py-3 text-[var(--accent-red)]">
        <strong>Error:</strong> {error.message}
      </div>
    );
  }

  const accounts = data?.accounts || [];

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="resend-caption mb-3 uppercase tracking-[0]">
            Account registry
          </p>
          <h1 className="resend-display text-5xl tracking-[0] sm:text-6xl">
            Accounts
          </h1>
        </div>
        <Button onClick={handleAddAccount}>
          <Plus size={16} />
          Add New Account
        </Button>
      </div>

      {accounts.length === 0 ? (
        <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
          <h3 className="mb-2 text-lg font-medium tracking-[0] text-[var(--ink)]">
            No Accounts Yet
          </h3>
          <p className="mb-4 text-[var(--body)]">
            Create your first account to start tracking your assets.
          </p>
          <Button onClick={handleAddAccount}>
            <Plus size={16} />
            Create First Account
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      )}

      {/* Modals */}
      <AddAccountModal isOpen={modal === "add-account"} onClose={closeModal} />
      <AddTransactionModal
        isOpen={modal === "add-transaction"}
        onClose={closeModal}
        defaultAccountId={accountId ? parseInt(accountId) : undefined}
      />
      <TransferModal
        isOpen={modal === "transfer"}
        onClose={closeModal}
        defaultFromAccountId={accountId ? parseInt(accountId) : undefined}
      />
      <ExchangeModal
        isOpen={modal === "exchange"}
        onClose={closeModal}
        defaultAccountId={accountId ? parseInt(accountId) : undefined}
      />
      <BuySellModal
        isOpen={modal === "buy"}
        onClose={closeModal}
        defaultAccountId={accountId ? parseInt(accountId) : undefined}
        defaultType="Buy"
      />
      <BuySellModal
        isOpen={modal === "sell"}
        onClose={closeModal}
        defaultAccountId={accountId ? parseInt(accountId) : undefined}
        defaultType="Sell"
      />
      {modal === "delete-account" && accountToDelete && (
        <DeleteAccountModal
          isOpen={true}
          onClose={closeModal}
          account={accountToDelete}
        />
      )}
    </div>
  );
}

export default function AccountsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center items-center h-64">
          <Spinner size="lg" />
        </div>
      }
    >
      <AccountsContent />
    </Suspense>
  );
}
