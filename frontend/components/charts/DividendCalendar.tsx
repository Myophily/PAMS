'use client';

interface Dividend {
  date: string;
  ticker: string;
  amount: number;
}

interface DividendCalendarProps {
  dividends: Dividend[];
  year?: number;
  month?: number;
}

export function DividendCalendar({
  dividends,
  year = new Date().getFullYear(),
  month = new Date().getMonth() + 1,
}: DividendCalendarProps) {
  // Get days in month
  const daysInMonth = new Date(year, month, 0).getDate();
  const firstDayOfMonth = new Date(year, month - 1, 1).getDay();

  // Create dividend map by date
  const dividendsByDate = dividends.reduce((acc, div) => {
    const date = new Date(div.date);
    if (date.getFullYear() === year && date.getMonth() + 1 === month) {
      const day = date.getDate();
      if (!acc[day]) acc[day] = [];
      acc[day].push(div);
    }
    return acc;
  }, {} as Record<number, Dividend[]>);

  // Create calendar grid
  const weeks: (number | null)[][] = [];
  let currentWeek: (number | null)[] = [];

  // Fill first week with empty days
  for (let i = 0; i < firstDayOfMonth; i++) {
    currentWeek.push(null);
  }

  // Fill days
  for (let day = 1; day <= daysInMonth; day++) {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  // Fill last week
  if (currentWeek.length > 0) {
    while (currentWeek.length < 7) {
      currentWeek.push(null);
    }
    weeks.push(currentWeek);
  }

  const monthName = new Date(year, month - 1).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
  });

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
        Dividend Calendar - {monthName}
      </h3>
      <div className="grid grid-cols-7 gap-1">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="py-2 text-center text-xs font-medium text-[var(--charcoal)]"
          >
            {day}
          </div>
        ))}

        {weeks.map((week, weekIndex) =>
          week.map((day, dayIndex) => {
            const hasDividend = day && dividendsByDate[day];
            const dividendTotal = hasDividend
              ? dividendsByDate[day].reduce((sum, div) => sum + div.amount, 0)
              : 0;

            return (
              <div
                key={`${weekIndex}-${dayIndex}`}
                className={`min-h-[60px] p-1 border rounded ${
                  day
                    ? hasDividend
                      ? 'border-[rgba(17,255,153,0.35)] bg-[rgba(17,255,153,0.1)]'
                      : 'border-[var(--hairline)] bg-[var(--surface-card)]'
                    : 'border-transparent bg-[rgba(255,255,255,0.03)]'
                }`}
              >
                {day && (
                  <>
                    <div className="text-xs font-medium text-[var(--body)]">
                      {day}
                    </div>
                    {hasDividend && (
                      <div className="text-xs mt-1">
                        <div className="font-medium text-[var(--accent-green)]">
                          ₩{dividendTotal.toLocaleString()}
                        </div>
                        {dividendsByDate[day].map((div, idx) => (
                          <div
                            key={idx}
                            className="truncate text-[var(--charcoal)]"
                            title={`${div.ticker}: ₩${div.amount.toLocaleString()}`}
                          >
                            {div.ticker}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
