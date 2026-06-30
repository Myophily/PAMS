import { forwardRef } from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="mb-1 block text-sm font-medium tracking-[0] text-[var(--body)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`h-10 w-full rounded-lg border bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--ink)] placeholder:text-[var(--stone)] focus:border-[var(--ink)] focus:outline-none ${
            error
              ? 'border-[rgba(255,32,71,0.62)]'
              : 'border-[var(--hairline-strong)]'
          } ${className}`}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-[var(--accent-red)]">{error}</p>
        )}
        {!error && helperText && (
          <p className="mt-1 text-sm text-[var(--mute)]">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
