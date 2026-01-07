'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { parseDecimal } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

interface AssetAllocationChartProps {
  data: Array<{ type: string; value_krw: DecimalString; percent: DecimalString }>;
}

export function AssetAllocationChart({ data }: AssetAllocationChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Asset Allocation</h3>
        <div className="flex items-center justify-center h-[300px] text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  // Transform DecimalString to number for chart library
  const chartData = data.map((item) => ({
    type: item.type,
    value_krw: parseDecimal(item.value_krw),
    percent: parseDecimal(item.percent),
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Asset Allocation</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={(entry: any) => `${entry.type} ${entry.percent.toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value_krw"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined) => value ? `₩${value.toLocaleString()}` : ''}
            contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
