'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { parseDecimal } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

interface TopAssetsBarChartProps {
  assets: Array<{
    ticker: string;
    name: string;
    value_krw: DecimalString;
    percent: DecimalString;
  }>;
}

export function TopAssetsBarChart({ assets }: TopAssetsBarChartProps) {
  if (!assets || assets.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold mb-4">Top Assets</h3>
        <div className="flex items-center justify-center h-[300px] text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  // Transform DecimalString to number for chart library and sort
  const chartData = [...assets]
    .map((item) => ({
      ticker: item.ticker,
      name: item.name,
      value_krw: parseDecimal(item.value_krw),
      percent: parseDecimal(item.percent),
    }))
    .sort((a, b) => b.value_krw - a.value_krw)
    .slice(0, 10);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Top Assets</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis
            dataKey="ticker"
            type="category"
            width={100}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number | undefined) => value ? `₩${value.toLocaleString()}` : ''}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          />
          <Bar dataKey="value_krw" fill="#3B82F6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
