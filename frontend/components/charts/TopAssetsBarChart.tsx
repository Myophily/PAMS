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
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
          Top Assets
        </h3>
        <div className="flex h-[300px] items-center justify-center text-[var(--mute)]">
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
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
        Top Assets
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
          <XAxis
            type="number"
            tick={{ fill: 'rgba(252,253,255,0.7)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            tickLine={{ stroke: 'rgba(255,255,255,0.14)' }}
          />
          <YAxis
            dataKey="ticker"
            type="category"
            width={100}
            tick={{ fill: 'rgba(252,253,255,0.7)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            tickLine={{ stroke: 'rgba(255,255,255,0.14)' }}
          />
          <Tooltip
            formatter={(value: number | undefined) => value ? `₩${value.toLocaleString()}` : ''}
            contentStyle={{
              backgroundColor: '#0a0a0c',
              border: '1px solid rgba(255,255,255,0.14)',
              borderRadius: '8px',
              color: '#fcfdff',
            }}
          />
          <Bar dataKey="value_krw" fill="#3b9eff" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
