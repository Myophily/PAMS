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
          <label className="block text-sm font-medium text-gray-900 mb-1">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`w-full border rounded px-3 py-2 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            error ? 'border-red-500' : 'border-gray-300'
          } ${className}`}
          {...props}
        />
        {error && <p className="text-red-500 text-sm mt-1">{error}</p>}
        {!error && helperText && <p className="text-gray-500 text-sm mt-1">{helperText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
