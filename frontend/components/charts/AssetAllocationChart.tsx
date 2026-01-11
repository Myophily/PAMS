'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { parseDecimal } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

const ASSET_COLORS: Record<string, string> = {
  Stock: '#F97316',
  Crypto: '#EF4444',
  Cash: '#3B82F6',
  Bond: '#86EFAC',
  Gold: '#22C55E',
};

interface AssetAllocationChartProps {
  data: Array<{ type: string; value_krw: DecimalString; percent: DecimalString }>;
  riskSummary?: {
    risk_assets_percent: DecimalString;
    safe_assets_percent: DecimalString;
  };
}

interface ChartDataEntry {
  type: string;
  value_krw: number;
  percent: number;
}

export function AssetAllocationChart({ data, riskSummary }: AssetAllocationChartProps) {
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

  const chartData = data.map((item) => ({
    type: item.type,
    value_krw: parseDecimal(item.value_krw),
    percent: parseDecimal(item.percent),
  }));

  const riskPercent = riskSummary ? parseDecimal(riskSummary.risk_assets_percent) : 0;
  const safePercent = riskSummary ? parseDecimal(riskSummary.safe_assets_percent) : 0;

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
            label={(props) => {
              const payload = props.payload as ChartDataEntry | undefined;
              if (!payload) return '';
              return `${payload.type} ${payload.percent.toFixed(1)}%`;
            }}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value_krw"
          >
            {chartData.map((entry) => (
              <Cell key={`cell-${entry.type}`} fill={ASSET_COLORS[entry.type] || '#8884d8'} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined) => value ? `₩${value.toLocaleString()}` : ''}
            contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '4px' }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      {riskSummary && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-center gap-8 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="font-medium">Risk Assets: {riskPercent.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="font-medium">Safe Assets: {safePercent.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
