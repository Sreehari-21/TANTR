import type { Grade } from '@/lib/api';
import { cn, scoreBg, scoreColor } from '@/lib/utils';
import Card from '@/components/ui/Card';

export type RubricMeta = {
  weights?: Record<string, number>;
  explanations?: Record<string, string>;
  difficulty?: { level?: string; multiplier?: number };
  metrics_final?: number;
  ai_score?: number | null;
  ai_blend?: number;
  ai_source?: string;
};

const METRICS: { key: keyof Grade; label: string; weightKey: string }[] = [
  { key: 'code_quality', label: 'Code Quality', weightKey: 'code_quality' },
  { key: 'efficiency', label: 'Efficiency', weightKey: 'efficiency' },
  { key: 'documentation', label: 'Documentation', weightKey: 'documentation' },
  { key: 'testing', label: 'Testing', weightKey: 'testing' },
  { key: 'commit_consistency', label: 'Consistency', weightKey: 'commit_consistency' },
];

function weightLabel(weights: Record<string, number> | undefined, key: string, fallback: string): string {
  if (weights && typeof weights[key] === 'number') {
    return `${Math.round(weights[key] * 100)}%`;
  }
  return fallback;
}

function ScoreBar({
  label,
  value,
  weight,
  explanation,
}: {
  label: string;
  value: number | null;
  weight: string;
  explanation?: string;
}) {
  const v = value ?? 0;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className={cn('font-mono font-medium', scoreColor(v))}>
          {v.toFixed(0)} <span className="text-slate-600">({weight})</span>
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-violet-950/80">
        <div
          className={cn(
            'h-full rounded-full bg-gradient-to-r transition-all duration-700',
            v >= 80
              ? 'from-cyan-500 to-violet-400'
              : v >= 60
                ? 'from-amber-500 to-orange-400'
                : 'from-rose-500 to-fuchsia-500'
          )}
          style={{
            width: `${Math.min(100, v)}%`,
            boxShadow: v >= 60 ? '0 0 8px rgba(34,211,238,0.4)' : undefined,
          }}
        />
      </div>
      {explanation && <p className="text-xs leading-relaxed text-slate-500">{explanation}</p>}
    </div>
  );
}

export default function GradeDisplay({
  grade,
  rubric,
}: {
  grade: Grade;
  rubric?: RubricMeta | null;
}) {
  const final = grade.final_score;
  const weights = rubric?.weights;
  const explanations = rubric?.explanations || {};
  const difficulty = rubric?.difficulty?.level;

  return (
    <Card className="animate-slide-up border-cyan-500/10">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <p className="font-mono text-xs uppercase tracking-widest text-cyan-400/70">◈ Mission report</p>
        {difficulty && (
          <span className="rounded-full border border-violet-500/25 bg-violet-500/10 px-2.5 py-0.5 font-mono text-xs text-violet-300">
            difficulty: {difficulty}
          </span>
        )}
      </div>

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
          {rubric?.ai_blend != null && rubric.ai_blend > 0 && (
            <p className="mt-3 max-w-[9rem] text-center font-mono text-[10px] text-slate-600">
              metrics {Math.round((1 - rubric.ai_blend) * 100)}% · AI {Math.round(rubric.ai_blend * 100)}%
            </p>
          )}
        </div>

        <div className="flex-1 space-y-4">
          {METRICS.map((m) => (
            <ScoreBar
              key={m.key}
              label={m.label}
              value={grade[m.key] as number | null}
              weight={weightLabel(weights, m.weightKey, '—')}
              explanation={explanations[m.weightKey]}
            />
          ))}
        </div>
      </div>

      {(explanations.final || explanations.difficulty) && (
        <div className="mt-6 space-y-2 border-t border-violet-500/10 pt-4">
          {explanations.difficulty && (
            <p className="text-sm text-slate-400">{explanations.difficulty}</p>
          )}
          {explanations.final && (
            <p className="text-sm text-slate-400">{explanations.final}</p>
          )}
          {rubric?.ai_score != null && (
            <p className="font-mono text-xs text-slate-600">
              AI overall: {rubric.ai_score.toFixed(1)}
              {rubric.ai_source ? ` · source=${rubric.ai_source}` : ''}
              {rubric.metrics_final != null ? ` · metrics-only=${rubric.metrics_final.toFixed(1)}` : ''}
            </p>
          )}
        </div>
      )}
    </Card>
  );
}
