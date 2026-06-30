import { forwardRef } from 'react';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options?: Array<{ value: string; label: string }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, options, className = '', children, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="mb-1 block text-sm font-medium tracking-[0] text-[var(--body)]">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={`h-10 w-full rounded-lg border bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--ink)] focus:border-[var(--ink)] focus:outline-none ${
            error
              ? 'border-[rgba(255,32,71,0.62)]'
              : 'border-[var(--hairline-strong)]'
          } ${className}`}
          {...props}
        >
          {options
            ? options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))
            : children}
        </select>
        {error && (
          <p className="mt-1 text-sm text-[var(--accent-red)]">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
