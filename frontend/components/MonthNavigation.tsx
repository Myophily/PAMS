'use client';

import { MonthOption } from '@/lib/types';
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
    <div className="bg-white rounded-lg shadow p-4">
      <div className="grid grid-cols-[auto_1fr_auto] gap-4 items-center">
        {/* Previous Button */}
        <Button
          variant="ghost"
          size="md"
          onClick={() => prevMonth && onMonthChange(prevMonth)}
          disabled={!hasPrev || disabled}
          className="whitespace-nowrap"
        >
          <span className="hidden sm:inline">← Previous</span>
          <span className="sm:hidden">←</span>
        </Button>

        {/* Month Dropdown */}
        <Select
          value={currentMonth}
          onChange={(e) => onMonthChange(e.target.value)}
          disabled={disabled}
          className="text-center font-semibold"
          options={availableMonths}
        />

        {/* Next Button */}
        <Button
          variant="ghost"
          size="md"
          onClick={() => nextMonth && onMonthChange(nextMonth)}
          disabled={!hasNext || disabled}
          className="whitespace-nowrap"
        >
          <span className="hidden sm:inline">Next →</span>
          <span className="sm:hidden">→</span>
        </Button>
      </div>

      {disabled && (
        <p className="text-sm text-gray-500 mt-2 text-center">
          Monthly navigation disabled while date range filter is active
        </p>
      )}
    </div>
  );
}
