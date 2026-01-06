'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
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
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold mb-4">Asset Growth</h3>
        <div className="flex items-center justify-center h-[400px] text-gray-500">
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
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Asset Growth</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="displayDate"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `₩${(value / 1000000).toFixed(1)}M`}
          />
          <Tooltip
            formatter={(value: number | undefined) => value ? `₩${value.toLocaleString()}` : ''}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="gain_loss"
            fill="#10B981"
            fillOpacity={0.2}
            stroke="none"
            name="Gain/Loss"
          />
          <Line
            type="monotone"
            dataKey="total_assets"
            stroke="#3B82F6"
            strokeWidth={2}
            name="Total Assets"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="principal"
            stroke="#6B7280"
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
