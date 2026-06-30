'use client';

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { parseDecimal } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

const ASSET_COLORS: Record<string, string> = {
  Stock: '#ff801f',
  Crypto: '#ff2047',
  Cash: '#3b9eff',
  Bond: '#11ff99',
  Gold: '#ffc53d',
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
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
          Asset Allocation
        </h3>
        <div className="flex h-[300px] items-center justify-center text-[var(--mute)]">
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
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
        Asset Allocation
      </h3>
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
            contentStyle={{
              backgroundColor: '#0a0a0c',
              border: '1px solid rgba(255,255,255,0.14)',
              borderRadius: '8px',
              color: '#fcfdff',
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      {riskSummary && (
        <div className="mt-4 border-t border-[var(--hairline)] pt-4">
          <div className="flex justify-center gap-8 text-sm">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-[var(--accent-red)]"></div>
              <span className="font-medium text-[var(--body)]">Risk Assets: {riskPercent.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-[var(--accent-blue)]"></div>
              <span className="font-medium text-[var(--body)]">Safe Assets: {safePercent.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
