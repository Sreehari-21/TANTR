import type { Grade } from '@/lib/api';

const METRICS: { key: keyof Grade; label: string; color: string }[] = [
  { key: 'code_quality', label: 'Code Quality', color: 'from-indigo-500 to-violet-500' },
  { key: 'efficiency', label: 'Efficiency', color: 'from-cyan-500 to-blue-500' },
  { key: 'documentation', label: 'Documentation', color: 'from-emerald-500 to-teal-500' },
  { key: 'testing', label: 'Testing', color: 'from-amber-500 to-orange-500' },
  { key: 'commit_consistency', label: 'Consistency', color: 'from-pink-500 to-rose-500' },
];

function scoreColor(score: number) {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 60) return 'text-amber-400';
  return 'text-red-400';
}

export default function GradeBreakdown({ grade }: { grade: Grade }) {
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">Final Score</p>
          <p className={`text-5xl font-bold tracking-tight ${scoreColor(grade.final_score)}`}>
            {grade.final_score.toFixed(1)}
          </p>
        </div>
        <div className="text-right text-sm text-slate-500">out of 100</div>
      </div>

      <div className="space-y-3">
        {METRICS.map(({ key, label, color }) => {
          const val = grade[key];
          const score = typeof val === 'number' ? val : 0;
          return (
            <div key={key}>
              <div className="mb-1 flex justify-between text-sm">
                <span className="text-slate-400">{label}</span>
                <span className="font-medium text-slate-200">{score.toFixed(0)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700`}
                  style={{ width: `${Math.min(100, score)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
