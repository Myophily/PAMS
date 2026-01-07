'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useDeleteAccount } from '@/lib/hooks/useAccounts';
import { formatCurrency } from '@/lib/utils/format';
import type { AccountWithBalance } from '@/lib/types';

interface DeleteAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  account: AccountWithBalance;
}

export function DeleteAccountModal({
  isOpen,
  onClose,
  account,
}: DeleteAccountModalProps) {
  const router = useRouter();
  const deleteAccount = useDeleteAccount();
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  // User must type account name to confirm
  const isConfirmed = confirmText === account.name;

  const handleDelete = async () => {
    if (!isConfirmed) return;

    setIsDeleting(true);
    try {
      await deleteAccount.mutateAsync(account.id);
      toast.success(`Account "${account.name}" deleted successfully`);
      router.push('/accounts'); // Redirect to account list
      onClose();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to delete account'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    setConfirmText('');
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Delete Account">
      <div className="space-y-4">
        {/* Warning Banner */}
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg
              className="w-6 h-6 text-red-600 mr-3 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <h4 className="text-red-800 font-bold text-lg mb-2">
                Warning: This action cannot be undone
              </h4>
              <p className="text-red-700 text-sm mb-2">
                Deleting this account will permanently remove:
              </p>
              <ul className="list-disc list-inside text-red-700 text-sm space-y-1 ml-2">
                <li>
                  <strong>All transactions</strong> in this account
                </li>
                <li>
                  <strong>All holdings</strong> ({account.holdings_count} items)
                </li>
                <li>
                  <strong>Account balance:</strong>{' '}
                  {formatCurrency(account.balance, account.currency as 'KRW' | 'USD')}
                </li>
              </ul>
              <p className="text-red-700 text-sm mt-3 font-semibold">
                Linked transactions in other accounts will be preserved but unlinked.
              </p>
            </div>
          </div>
        </div>

        {/* Account Summary */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h5 className="font-semibold text-gray-900 mb-2">
            Account to Delete:
          </h5>
          <div className="space-y-1 text-sm">
            <div>
              <span className="text-gray-600">Name:</span>{' '}
              <span className="font-semibold text-gray-900">{account.name}</span>
            </div>
            <div>
              <span className="text-gray-600">Type:</span>{' '}
              <span className="text-gray-900">{account.type}</span>
            </div>
            <div>
              <span className="text-gray-600">Balance:</span>{' '}
              <span className="text-gray-900">
                {formatCurrency(account.balance, account.currency as 'KRW' | 'USD')}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Holdings:</span>{' '}
              <span className="text-gray-900">{account.holdings_count} items</span>
            </div>
          </div>
        </div>

        {/* Confirmation Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type <span className="font-bold text-red-600">{account.name}</span> to
            confirm deletion
          </label>
          <Input
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="Enter account name exactly"
            className={confirmText && !isConfirmed ? 'border-red-300' : ''}
          />
          {confirmText && !isConfirmed && (
            <p className="text-red-600 text-sm mt-1">
              Account name does not match
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end pt-2">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            disabled={!isConfirmed || isDeleting}
            loading={isDeleting}
          >
            Delete Account Permanently
          </Button>
        </div>
      </div>
    </Modal>
  );
}
