'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';

import type { MonthOption } from '@/lib/types';
import { getAdjacentMonth } from '@/lib/utils/month';
import { Button } from './ui/Button';
import { Select } from './ui/Select';

interface MonthNavigationProps {
  availableMonths: MonthOption[];
  currentMonth: string;
  onMonthChange: (month: string) => void;
  disabled?: boolean;
}

export function MonthNavigation({
  availableMonths,
  currentMonth,
  onMonthChange,
  disabled = false
}: MonthNavigationProps) {
  const monthValues = availableMonths.map(m => m.value);
  const prevMonth = getAdjacentMonth(currentMonth, monthValues, 'prev');
  const nextMonth = getAdjacentMonth(currentMonth, monthValues, 'next');

  const hasPrev = prevMonth !== null;
  const hasNext = nextMonth !== null;

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4">
      <div className="grid grid-cols-[auto_1fr_auto] gap-4 items-center">
        <Button
          variant="ghost"
          size="md"
          onClick={() => prevMonth && onMonthChange(prevMonth)}
          disabled={!hasPrev || disabled}
          className="whitespace-nowrap"
        >
          <ChevronLeft size={16} />
          <span className="hidden sm:inline">Previous</span>
          <span className="sm:hidden">Prev</span>
        </Button>

        <Select
          value={currentMonth}
          onChange={(e) => onMonthChange(e.target.value)}
          disabled={disabled}
          className="text-center font-semibold"
          options={availableMonths}
        />

        <Button
          variant="ghost"
          size="md"
          onClick={() => nextMonth && onMonthChange(nextMonth)}
          disabled={!hasNext || disabled}
          className="whitespace-nowrap"
        >
          <span>Next</span>
          <ChevronRight size={16} />
        </Button>
      </div>

      {disabled && (
        <p className="mt-2 text-center text-sm text-[var(--mute)]">
          Monthly navigation disabled while date range filter is active
        </p>
      )}
    </div>
  );
}
