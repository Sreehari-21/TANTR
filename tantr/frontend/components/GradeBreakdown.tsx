import Card from '@/components/ui/Card';
import type { RubricMeta } from '@/components/GradeDisplay';

/** Detailed professor rubric breakdown (weights + narrative). */
export default function GradeBreakdown({ rubric }: { rubric?: RubricMeta | null }) {
  if (!rubric?.weights && !rubric?.explanations) return null;

  const weights = rubric.weights || {};
  const entries = Object.entries(weights);

  return (
    <Card className="mb-6 border-violet-500/10" padding="md">
      <h2 className="mb-3 text-lg font-semibold text-white">Rubric breakdown</h2>
      <p className="mb-4 text-sm text-slate-500">
        How the professor engine weighted this transmission.
      </p>
      {entries.length > 0 && (
        <ul className="mb-4 grid gap-2 sm:grid-cols-2">
          {entries.map(([key, value]) => (
            <li
              key={key}
              className="flex items-center justify-between rounded-xl border border-violet-500/10 bg-violet-500/5 px-3 py-2 text-sm"
            >
              <span className="capitalize text-slate-300">{key.replace(/_/g, ' ')}</span>
              <span className="font-mono text-cyan-400">{Math.round(value * 100)}%</span>
            </li>
          ))}
        </ul>
      )}
      {rubric.explanations?.difficulty && (
        <p className="text-sm text-slate-400">{rubric.explanations.difficulty}</p>
      )}
    </Card>
  );
}
