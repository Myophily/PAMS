interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div
      className={`rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6 text-[var(--body)] ${className}`}
    >
      {children}
    </div>
  );
}
