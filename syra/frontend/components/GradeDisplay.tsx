import type { Grade } from '@/lib/api';
import { cn, scoreBg, scoreColor } from '@/lib/utils';
import Card from '@/components/ui/Card';

const METRICS: { key: keyof Grade; label: string; weight: string }[] = [
  { key: 'code_quality', label: 'Code Quality', weight: '30%' },
  { key: 'efficiency', label: 'Efficiency', weight: '25%' },
  { key: 'documentation', label: 'Documentation', weight: '20%' },
  { key: 'testing', label: 'Testing', weight: '15%' },
  { key: 'commit_consistency', label: 'Consistency', weight: '10%' },
];

function ScoreBar({ label, value, weight }: { label: string; value: number | null; weight: string }) {
  const v = value ?? 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className={cn('font-mono font-medium', scoreColor(v))}>
          {v.toFixed(0)} <span className="text-slate-600">({weight})</span>
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-violet-950/80">
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-700',
            v >= 80 ? 'from-cyan-500 to-violet-400' : v >= 60 ? 'from-amber-500 to-orange-400' : 'from-rose-500 to-fuchsia-500'
          )}
          style={{ width: `${Math.min(100, v)}%`, boxShadow: v >= 60 ? '0 0 8px rgba(34,211,238,0.4)' : undefined }}
        />
      </div>
    </div>
  );
}

export default function GradeDisplay({ grade }: { grade: Grade }) {
  const final = grade.final_score;
  return (
    <Card className="animate-slide-up border-cyan-500/10">
      <p className="mb-4 font-mono text-xs uppercase tracking-widest text-cyan-400/70">◈ Mission report</p>
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
        <div className="relative flex shrink-0 flex-col items-center">
          <div className="absolute inset-0 animate-pulse-soft rounded-full bg-cyan-500/10 blur-xl" />
          <div
            className={cn(
              'relative flex h-32 w-32 flex-col items-center justify-center rounded-full border border-violet-500/20 bg-gradient-to-br',
              scoreBg(final)
            )}
            style={{ boxShadow: '0 0 40px rgba(139, 92, 246, 0.2)' }}
          >
            <span className={cn('text-4xl font-bold', scoreColor(final))}>{final.toFixed(1)}</span>
            <span className="font-mono text-xs text-slate-500">/ 100</span>
          </div>
        </div>
        <div className="flex-1 space-y-3">
          {METRICS.map((m) => (
            <ScoreBar key={m.key} label={m.label} value={grade[m.key] as number | null} weight={m.weight} />
          ))}
        </div>
      </div>
    </Card>
  );
}
