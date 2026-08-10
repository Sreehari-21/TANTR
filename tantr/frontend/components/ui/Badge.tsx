import { cn } from '@/lib/utils';

type Variant = 'default' | 'success' | 'warning' | 'error' | 'info';

const styles: Record<Variant, string> = {
  default: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
  success: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/25 shadow-[0_0_8px_rgba(34,211,238,0.1)]',
  warning: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
  error: 'bg-rose-500/10 text-rose-300 border-rose-500/20',
  info: 'bg-violet-500/10 text-violet-300 border-violet-500/20',
};

export default function Badge({
  children,
  variant = 'default',
  className,
}: {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 font-mono text-xs font-medium',
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
