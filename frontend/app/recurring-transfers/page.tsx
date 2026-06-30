"use client";

import { useState } from "react";
import { Pause, Play, Plus, Repeat2, Trash2 } from "lucide-react";
import { toast } from "sonner";

import {
  useRecurringTransfers,
  useDeleteRecurringTransfer,
  useUpdateRecurringTransfer,
} from "@/lib/hooks/useRecurringTransfers";
import { Button } from "@/components/ui/Button";
import { RecurringTransferModal } from "@/components/modals/RecurringTransferModal";
import { formatDecimal } from "@/lib/utils/decimal";

export default function RecurringTransfersPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: transfers, isLoading } = useRecurringTransfers();
  const deleteTransfer = useDeleteRecurringTransfer();
  const updateTransfer = useUpdateRecurringTransfer();

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    try {
      await updateTransfer.mutateAsync({
        id,
        data: { is_active: !currentStatus },
      });
      toast.success(
        currentStatus
          ? "Recurring transfer paused"
          : "Recurring transfer resumed"
      );
    } catch {
      toast.error("Failed to update transfer status");
    }
  };

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        "Are you sure you want to delete this recurring transfer? This will not affect historical transactions."
      )
    ) {
      return;
    }

    try {
      await deleteTransfer.mutateAsync(id);
      toast.success("Recurring transfer deleted");
    } catch {
      toast.error("Failed to delete recurring transfer");
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-[var(--mute)]">Loading recurring transfers...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="resend-caption mb-3 uppercase tracking-[0]">
            Automation
          </p>
          <h1 className="resend-display text-5xl tracking-[0] sm:text-6xl">
            Recurring Transfers
          </h1>
          <p className="mt-3 text-[var(--charcoal)]">
            Manage automatic monthly transfers between accounts
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={16} />
          Create New
        </Button>
      </div>

      {!transfers || transfers.length === 0 ? (
        <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-8 text-center">
          <div className="mb-4 text-[var(--mute)]">
            <Repeat2 className="mx-auto h-12 w-12" />
          </div>
          <h3 className="mb-2 text-lg font-medium tracking-[0] text-[var(--ink)]">
            No recurring transfers
          </h3>
          <p className="mb-4 text-[var(--charcoal)]">
            Create your first recurring transfer to automatically move money
            between accounts each month.
          </p>
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus size={16} />
            Create Recurring Transfer
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {transfers.map((transfer) => (
            <div
              key={transfer.id}
              className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6 transition hover:border-[rgba(252,253,255,0.28)]"
            >
              <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-lg font-medium tracking-[0] text-[var(--ink)]">
                      {transfer.from_account_name} → {transfer.to_account_name}
                    </h3>
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium tracking-[0] ${
                        transfer.is_active
                          ? "border-[rgba(17,255,153,0.35)] bg-[rgba(17,255,153,0.1)] text-[var(--accent-green)]"
                          : "border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--charcoal)]"
                      }`}
                    >
                      {transfer.is_active ? "Active" : "Paused"}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 gap-4 text-sm text-[var(--charcoal)] sm:grid-cols-2">
                    <div>
                      <span className="font-medium text-[var(--body)]">Amount:</span>{" "}
                      <span className="font-mono font-semibold text-[var(--ink)]">
                        {formatDecimal(transfer.amount)} KRW
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-[var(--body)]">
                        Day of Month:
                      </span>{" "}
                      <span className="text-[var(--ink)]">
                        {transfer.day_of_month}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-[var(--body)]">
                        Last Executed:
                      </span>{" "}
                      <span className="text-[var(--ink)]">
                        {formatDate(transfer.last_executed_date)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-[var(--body)]">
                        Next Execution:
                      </span>{" "}
                      <span className="text-[var(--ink)]">
                        {formatDate(transfer.next_execution_date)}
                      </span>
                    </div>
                  </div>

                  {transfer.description && (
                    <p className="mt-3 text-sm text-[var(--charcoal)]">
                      <span className="font-medium text-[var(--body)]">Note:</span>{" "}
                      {transfer.description}
                    </p>
                  )}
                </div>

                <div className="flex flex-row gap-2 lg:ml-6 lg:flex-col">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      handleToggleActive(transfer.id, transfer.is_active)
                    }
                    disabled={updateTransfer.isPending}
                  >
                    {transfer.is_active ? <Pause size={14} /> : <Play size={14} />}
                    {transfer.is_active ? "Pause" : "Resume"}
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(transfer.id)}
                    disabled={deleteTransfer.isPending}
                  >
                    <Trash2 size={14} />
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <RecurringTransferModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
