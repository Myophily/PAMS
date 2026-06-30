'use client';

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { parseDecimal } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

interface AssetVolatilityChartProps {
  data: Array<{
    date: string;
    total_assets: DecimalString;
    principal: DecimalString;
    gain_loss: DecimalString;
  }>;
}

export function AssetVolatilityChart({ data }: AssetVolatilityChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
          Asset Growth
        </h3>
        <div className="flex h-[400px] items-center justify-center text-[var(--mute)]">
          No data available
        </div>
      </div>
    );
  }

  // Transform DecimalString to number for chart library and format dates
  const chartData = data.map((item) => ({
    date: item.date,
    total_assets: parseDecimal(item.total_assets),
    principal: parseDecimal(item.principal),
    gain_loss: parseDecimal(item.gain_loss),
    displayDate: new Date(item.date).toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
    }),
  }));

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
        Asset Growth
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
          <XAxis
            dataKey="displayDate"
            tick={{ fill: 'rgba(252,253,255,0.7)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            tickLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: 'rgba(252,253,255,0.7)', fontSize: 12 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            tickLine={{ stroke: 'rgba(255,255,255,0.14)' }}
            tickFormatter={(value) => `₩${(value / 1000000).toFixed(1)}M`}
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
          <Legend wrapperStyle={{ color: 'rgba(252,253,255,0.7)' }} />
          <Area
            type="monotone"
            dataKey="gain_loss"
            fill="#11ff99"
            fillOpacity={0.14}
            stroke="none"
            name="Gain/Loss"
          />
          <Line
            type="monotone"
            dataKey="total_assets"
            stroke="#3b9eff"
            strokeWidth={2}
            name="Total Assets"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="principal"
            stroke="#a1a4a5"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Principal"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
