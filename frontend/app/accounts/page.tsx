"use client";

import { Suspense } from "react";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { AccountCard } from "./_components/AccountCard";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
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
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong>Error:</strong> {error.message}
      </div>
    );
  }

  const accounts = data?.accounts || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Accounts</h1>
        <Button onClick={handleAddAccount}>Add New Account</Button>
      </div>

      {accounts.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">No Accounts Yet</h3>
          <p className="text-gray-700 mb-4">
            Create your first account to start tracking your assets.
          </p>
          <Button onClick={handleAddAccount}>Create First Account</Button>
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
