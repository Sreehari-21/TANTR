import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import CodeEditor from '@/components/CodeEditor';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Spinner from '@/components/ui/Spinner';
import {
  getRepo,
  getCommits,
  createCommit,
  getRepoTree,
} from '@/lib/api';
import type { Repo, Commit } from '@/lib/api';
import { cn, formatRelative, shortSha } from '@/lib/utils';

const DEFAULT_CODE = `def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet("TANTR"))
`;

type Tab = 'code' | 'commits' | 'compose';

export default function RepoDetailPage() {
  const router = useRouter();
  const repoId = Number(router.query.id);

  const [repo, setRepo] = useState<Repo | null>(null);
  const [commits, setCommits] = useState<Commit[]>([]);
  const [treeFiles, setTreeFiles] = useState<Record<string, string>>({});
  const [headSha, setHeadSha] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>('code');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [error, setError] = useState('');

  // Compose state
  const [filePath, setFilePath] = useState('main.py');
  const [code, setCode] = useState(DEFAULT_CODE);
  const [message, setMessage] = useState('');
  const [committing, setCommitting] = useState(false);

  const load = useCallback(async () => {
    if (!repoId || Number.isNaN(repoId)) return;
    setError('');
    try {
      const [r, c, tree] = await Promise.all([
        getRepo(repoId),
        getCommits(repoId),
        getRepoTree(repoId),
      ]);
      setRepo(r);
      setCommits(c);
      setTreeFiles(tree.files || {});
      setHeadSha(tree.sha);
      const paths = Object.keys(tree.files || {}).sort();
      if (paths.length) {
        setSelectedPath((prev) => (prev && tree.files[prev] != null ? prev : paths[0]));
      } else {
        setSelectedPath(null);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load repository');
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => {
    const token = localStorage.getItem('tantr_token');
    if (!token) {
      router.replace('/login');
      return;
    }
    if (!router.isReady) return;
    load();
  }, [router, load]);

  const paths = useMemo(() => Object.keys(treeFiles).sort(), [treeFiles]);

  const handleCommit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoId || !message.trim()) return;
    setCommitting(true);
    setError('');
    try {
      const commit = await createCommit(repoId, {
        message: message.trim(),
        files: { [filePath.trim() || 'main.py']: code },
      });
      setMessage('');
      await load();
      setTab('commits');
      router.push(`/repos/${repoId}/commits/${commit.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Commit failed');
    } finally {
      setCommitting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <Spinner className="min-h-[50vh]" label="Loading repository..." />
      </Layout>
    );
  }

  if (!repo) {
    return (
      <Layout>
        <Card className="py-16 text-center">
          <p className="text-slate-400">{error || 'Repository not found'}</p>
          <Link href="/dashboard" className="mt-4 inline-block text-cyan-400 hover:underline">
            Back to dashboard
          </Link>
        </Card>
      </Layout>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'code', label: 'Code' },
    { id: 'commits', label: 'Commits' },
    { id: 'compose', label: 'New commit' },
  ];

  return (
    <Layout>
      <div className="mb-6">
        <Link href="/dashboard" className="font-mono text-xs text-slate-500 hover:text-cyan-400">
          ← Mission Control
        </Link>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan-400/80">◈ Repository</p>
            <h1 className="page-title">{repo.name}</h1>
            {repo.description && <p className="page-subtitle">{repo.description}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {headSha ? (
              <Badge variant="info">HEAD {shortSha(headSha)}</Badge>
            ) : (
              <Badge>empty</Badge>
            )}
            <Badge>{commits.length} commits</Badge>
          </div>
        </div>
      </div>

      <div className="mb-6 flex gap-1 border-b border-violet-500/15">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'px-4 py-2.5 text-sm font-medium transition-colors',
              tab === t.id
                ? 'border-b-2 border-cyan-400 text-cyan-300'
                : 'text-slate-500 hover:text-slate-300'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {tab === 'code' && (
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <Card padding="sm" className="h-fit">
            <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-slate-500">Files</p>
            {paths.length === 0 ? (
              <p className="text-sm text-slate-500">No files yet. Create a commit to seed the tree.</p>
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
            {selectedPath && treeFiles[selectedPath] != null ? (
              <>
                <div className="flex items-center justify-between border-b border-violet-500/15 px-4 py-2.5">
                  <span className="font-mono text-xs text-cyan-400/80">{selectedPath}</span>
                  <Button
                    variant="ghost"
                    className="!px-2 !py-1 text-xs"
                    onClick={() => {
                      setFilePath(selectedPath);
                      setCode(treeFiles[selectedPath]);
                      setTab('compose');
                    }}
                  >
                    Edit & commit
                  </Button>
                </div>
                <pre className="max-h-[560px] overflow-auto bg-[#0a0520]/60 p-4 font-mono text-sm leading-relaxed text-slate-300">
                  {treeFiles[selectedPath]}
                </pre>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <p className="text-slate-400">This repository has no files at HEAD.</p>
                <Button className="mt-4" onClick={() => setTab('compose')}>
                  Write first commit
                </Button>
              </div>
            )}
          </Card>
        </div>
      )}

      {tab === 'commits' && (
        <Card padding="none">
          {commits.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-slate-400">No commits yet.</p>
              <Button className="mt-4" onClick={() => setTab('compose')}>
                Create first commit
              </Button>
            </div>
          ) : (
            <ul className="divide-y divide-violet-500/10">
              {commits.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/repos/${repoId}/commits/${c.id}`}
                    className="flex flex-col gap-1 px-5 py-4 transition-colors hover:bg-violet-500/5 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div>
                      <p className="font-medium text-white">{c.message || '(no message)'}</p>
                      <p className="mt-1 font-mono text-xs text-slate-500">
                        {c.author_name || 'unknown'} · {formatRelative(c.created_at)}
                      </p>
                    </div>
                    <span className="font-mono text-xs text-cyan-400/70">{shortSha(c.sha)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {tab === 'compose' && (
        <form onSubmit={handleCommit} className="space-y-4">
          <Card>
            <p className="mb-4 font-mono text-xs uppercase tracking-widest text-cyan-400/70">
              ◈ Compose commit
            </p>
            <div className="mb-4 grid gap-4 sm:grid-cols-2">
              <Input
                label="File path"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="main.py"
                required
              />
              <Input
                label="Commit message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Add greeting helper"
                required
              />
            </div>
            <CodeEditor value={code} onChange={setCode} path={filePath || 'main.py'} height={420} />
            <div className="mt-4 flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setTab('code')}>
                Cancel
              </Button>
              <Button type="submit" loading={committing}>
                Commit & analyze
              </Button>
            </div>
          </Card>
        </form>
      )}
    </Layout>
  );
}
