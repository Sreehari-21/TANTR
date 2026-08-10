import { cn } from '@/lib/utils';

export default function Spinner({ className, label = 'Loading' }: { className?: string; label?: string }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-4', className)} role="status">
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-violet-500/20 border-t-cyan-400" />
        <div className="absolute inset-1 animate-spin rounded-full border border-violet-400/10 border-b-violet-400" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
        <div className="absolute inset-0 flex items-center justify-center text-xs text-cyan-400">✦</div>
      </div>
      <span className="font-mono text-xs uppercase tracking-widest text-slate-500">{label}</span>
    </div>
  );
}
