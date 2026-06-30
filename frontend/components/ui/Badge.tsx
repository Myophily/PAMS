interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'danger' | 'warning';
  className?: string;
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  const variants = {
    default:
      'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--body)]',
    success:
      'border-[rgba(17,255,153,0.35)] bg-[rgba(17,255,153,0.1)] text-[var(--accent-green)]',
    danger:
      'border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] text-[var(--accent-red)]',
    warning:
      'border-[rgba(255,197,61,0.38)] bg-[rgba(255,197,61,0.1)] text-[var(--accent-yellow)]',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium tracking-[0] ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
