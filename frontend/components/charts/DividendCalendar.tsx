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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Dividend Calendar - {monthName}</h3>
      <div className="grid grid-cols-7 gap-1">
        {/* Day headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="text-center text-xs font-medium text-gray-600 py-2"
          >
            {day}
          </div>
        ))}

        {/* Calendar days */}
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
                      ? 'bg-green-50 border-green-300'
                      : 'bg-white border-gray-200'
                    : 'bg-gray-50 border-transparent'
                }`}
              >
                {day && (
                  <>
                    <div className="text-xs font-medium text-gray-700">
                      {day}
                    </div>
                    {hasDividend && (
                      <div className="text-xs mt-1">
                        <div className="text-green-700 font-medium">
                          ₩{dividendTotal.toLocaleString()}
                        </div>
                        {dividendsByDate[day].map((div, idx) => (
                          <div
                            key={idx}
                            className="text-gray-600 truncate"
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
