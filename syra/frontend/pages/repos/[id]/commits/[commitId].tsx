import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import GradeDisplay, { type RubricMeta } from '@/components/GradeDisplay';
import GradeBreakdown from '@/components/GradeBreakdown';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Spinner from '@/components/ui/Spinner';
import {
  getCommitAnalysis,
  getCommitDiff,
  getCommitFiles,
  triggerAnalyze,
  type Commit,
  type CommitAnalysis,
  type Grade,
} from '@/lib/api';
import { cn, formatDate, shortSha } from '@/lib/utils';

type Loaded = Commit & { analysis?: CommitAnalysis; grade?: Grade };

function rubricFromAnalysis(analysis?: CommitAnalysis | null): RubricMeta | null {
  const raw = analysis?.static_analysis_raw as Record<string, unknown> | null | undefined;
  const rubric = raw?.rubric;
  if (!rubric || typeof rubric !== 'object') return null;
  return rubric as RubricMeta;
}

export default function CommitDetailPage() {
  const router = useRouter();
  const repoId = Number(router.query.id);
  const commitId = Number(router.query.commitId);

  const [data, setData] = useState<Loaded | null>(null);
  const [diff, setDiff] = useState('');
  const [files, setFiles] = useState<Record<string, string>>({});
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [view, setView] = useState<'feedback' | 'diff' | 'files'>('feedback');

  const load = useCallback(async () => {
    if (!repoId || !commitId || Number.isNaN(repoId) || Number.isNaN(commitId)) return;
    setError('');
    try {
      const [analysis, d, f] = await Promise.all([
        getCommitAnalysis(repoId, commitId),
        getCommitDiff(repoId, commitId).catch(() => ''),
        getCommitFiles(repoId, commitId).catch(() => ({ sha: '', files: {} })),
      ]);
      setData(analysis);
      setDiff(d);
      setFiles(f.files || {});
      const paths = Object.keys(f.files || {}).sort();
      setSelectedPath(paths[0] ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load commit');
    } finally {
      setLoading(false);
    }
  }, [repoId, commitId]);

  useEffect(() => {
    if (!localStorage.getItem('syra_token')) {
      router.replace('/login');
      return;
    }
    if (!router.isReady) return;
    load();
  }, [router, load]);

  // Poll while analysis pending
  useEffect(() => {
    const status = data?.analysis?.status;
    if (!status || status === 'completed' || status === 'failed') return;
    const t = setInterval(() => {
      load();
    }, 2500);
    return () => clearInterval(t);
  }, [data?.analysis?.status, load]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      await triggerAnalyze(repoId, commitId);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analyze failed');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <Spinner className="min-h-[50vh]" label="Loading commit..." />
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <Card className="py-16 text-center">
          <p className="text-slate-400">{error || 'Commit not found'}</p>
          <Link href={`/repos/${repoId}`} className="mt-4 inline-block text-cyan-400 hover:underline">
            Back to repository
          </Link>
        </Card>
      </Layout>
    );
  }

  const analysis = data.analysis;
  const grade = data.grade;
  const rubric = rubricFromAnalysis(analysis);
  const paths = Object.keys(files).sort();
  const pending = analysis && analysis.status !== 'completed' && analysis.status !== 'failed';

  return (
    <Layout>
      <div className="mb-6">
        <Link
          href={`/repos/${repoId}`}
          className="font-mono text-xs text-slate-500 hover:text-cyan-400"
        >
          ← Repository
        </Link>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan-400/80">◈ Commit</p>
            <h1 className="page-title text-2xl sm:text-3xl">{data.message || '(no message)'}</h1>
            <p className="mt-2 font-mono text-xs text-slate-500">
              {shortSha(data.sha)}
              {data.parent_sha ? ` · parent ${shortSha(data.parent_sha)}` : ' · root'}
              {' · '}
              {data.author_name || 'unknown'}
              {' · '}
              {formatDate(data.created_at)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {analysis ? (
              <Badge
                variant={
                  analysis.status === 'completed'
                    ? 'success'
                    : analysis.status === 'failed'
                      ? 'error'
                      : 'warning'
                }
              >
                {analysis.status}
              </Badge>
            ) : (
              <Badge>no analysis</Badge>
            )}
            <Button variant="secondary" loading={analyzing} onClick={handleAnalyze}>
              Re-analyze
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      <div className="mb-6 flex gap-1 border-b border-violet-500/15">
        {(
          [
            { id: 'feedback' as const, label: 'Feedback' },
            { id: 'diff' as const, label: 'Diff' },
            { id: 'files' as const, label: 'Files' },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setView(t.id)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium transition-colors',
              view === t.id
                ? 'border-b-2 border-cyan-400 text-cyan-300'
                : 'text-slate-500 hover:text-slate-300'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {view === 'feedback' && (
        <div className="space-y-6">
          {pending && (
            <Card className="flex items-center gap-4 border-amber-500/20 py-4">
              <div className="relative h-8 w-8 shrink-0">
                <div className="absolute inset-0 animate-spin rounded-full border-2 border-violet-500/20 border-t-cyan-400" />
              </div>
              <p className="text-sm text-amber-200/90">Professor engine is reviewing this commit…</p>
            </Card>
          )}

          {grade && <GradeDisplay grade={grade} rubric={rubric} />}
          <GradeBreakdown rubric={rubric} />

          {analysis?.ai_feedback && (
            <Card>
              <p className="mb-3 font-mono text-xs uppercase tracking-widest text-cyan-400/70">
                ◈ AI feedback
              </p>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                {analysis.ai_feedback}
              </p>
              {analysis.ai_suggestions && analysis.ai_suggestions.length > 0 && (
                <ul className="mt-4 list-inside list-disc space-y-1 text-sm text-slate-400">
                  {analysis.ai_suggestions.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              )}
            </Card>
          )}

          {!grade && !pending && (
            <Card className="py-12 text-center">
              <p className="text-slate-400">No grade yet for this commit.</p>
              <Button className="mt-4" loading={analyzing} onClick={handleAnalyze}>
                Run analysis
              </Button>
            </Card>
          )}

          {analysis?.warnings && analysis.warnings.length > 0 && (
            <Card className="border-amber-500/15">
              <p className="mb-2 text-sm font-medium text-amber-200">Warnings</p>
              <ul className="space-y-1 font-mono text-xs text-slate-400">
                {analysis.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}

      {view === 'diff' && (
        <Card padding="none" className="overflow-hidden">
          <pre className="max-h-[70vh] overflow-auto bg-[#0a0520]/80 p-4 font-mono text-xs leading-relaxed text-slate-300">
            {diff || 'No diff (empty or identical trees).'}
          </pre>
        </Card>
      )}

      {view === 'files' && (
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <Card padding="sm" className="h-fit">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-slate-500">
              Tree @ {shortSha(data.sha)}
            </p>
            {paths.length === 0 ? (
              <p className="text-sm text-slate-500">No files</p>
            ) : (
              <ul className="space-y-0.5">
                {paths.map((path) => (
                  <li key={path}>
                    <button
                      type="button"
                      onClick={() => setSelectedPath(path)}
                      className={cn(
                        'w-full rounded-lg px-2.5 py-1.5 text-left font-mono text-xs transition-colors',
                        selectedPath === path
                          ? 'bg-violet-500/20 text-cyan-300'
                          : 'text-slate-400 hover:bg-violet-500/10 hover:text-slate-200'
                      )}
                    >
                      {path}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <Card padding="none" className="overflow-hidden">
            {selectedPath && files[selectedPath] != null ? (
              <>
                <div className="border-b border-violet-500/15 px-4 py-2.5 font-mono text-xs text-cyan-400/80">
                  {selectedPath}
                </div>
                <pre className="max-h-[560px] overflow-auto bg-[#0a0520]/60 p-4 font-mono text-sm leading-relaxed text-slate-300">
                  {files[selectedPath]}
                </pre>
              </>
            ) : (
              <div className="py-16 text-center text-slate-500">Select a file</div>
            )}
          </Card>
        </div>
      )}
    </Layout>
  );
}
