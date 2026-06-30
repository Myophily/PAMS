import { Spinner } from './Spinner';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  children,
  className = '',
  ...props
}: ButtonProps) {
  const baseClasses =
    'inline-flex items-center justify-center gap-2 rounded-lg border font-medium tracking-[0] transition disabled:cursor-not-allowed disabled:opacity-50';

  const sizes = {
    sm: 'h-8 px-3 text-sm',
    md: 'h-9 px-4 text-sm',
    lg: 'h-11 px-5 text-base',
  };

  const variants = {
    primary:
      'border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-on)] hover:bg-[var(--surface-light)]',
    secondary:
      'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--ink)] hover:bg-[var(--surface-card)]',
    danger:
      'border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] text-[var(--accent-red)] hover:bg-[rgba(255,32,71,0.16)]',
    ghost:
      'border-transparent bg-transparent text-[var(--charcoal)] hover:border-[var(--hairline-strong)] hover:bg-[var(--surface-elevated)] hover:text-[var(--ink)]',
  };

  return (
    <button
      className={`${baseClasses} ${sizes[size]} ${variants[variant]} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? <Spinner size="sm" /> : children}
    </button>
  );
}
