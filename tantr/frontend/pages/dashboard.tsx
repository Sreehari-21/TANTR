import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { getRepos, createRepo, getMe } from '@/lib/api';
import type { Repo, User } from '@/lib/api';
import { formatRelative } from '@/lib/utils';

export default function Dashboard() {
  const router = useRouter();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('tantr_token');
    if (!token) {
      router.replace('/login');
      return;
    }
    Promise.all([getRepos(), getMe()])
      .then(([r, u]) => {
        setRepos(r);
        setUser(u);
      })
      .catch(() => router.replace('/login'))
      .finally(() => setLoading(false));
  }, [router]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setCreating(true);
    try {
      const repo = await createRepo({ name: newName, description: newDesc || undefined });
      setRepos((prev) => [repo, ...prev]);
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
      router.push(`/repos/${repo.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create repo');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <Spinner className="min-h-[50vh]" label="Initializing mission control..." />
      </Layout>
    );
  }

  const greeting = user?.full_name || user?.username;

  return (
    <Layout>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-cyan-400/80">◈ Mission Control</p>
          <h1 className="page-title">Greetings, {greeting}</h1>
          <p className="page-subtitle">Your fleet of code repositories awaits in deep space.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <span>🛸</span>
          Launch new station
        </Button>
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Active stations', value: repos.length, icon: '🪐', color: 'from-violet-600/20 to-violet-600/5' },
          { label: 'Systems online', value: repos.length > 0 ? 'Ready' : 'Standby', icon: '⚡', color: 'from-cyan-600/20 to-cyan-600/5' },
          { label: 'AI uplink', value: 'Connected', icon: '📡', color: 'from-fuchsia-600/20 to-fuchsia-600/5' },
        ].map((stat) => (
          <Card key={stat.label} padding="sm" className={`bg-gradient-to-br ${stat.color}`}>
            <div className="flex items-center gap-4">
              <span className="text-2xl">{stat.icon}</span>
              <div>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-slate-500">{stat.label}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#030014]/80 p-4 backdrop-blur-md">
          <Card className="w-full max-w-lg animate-slide-up border-violet-500/20" padding="lg">
            <p className="font-mono text-xs uppercase tracking-widest text-cyan-400/70">◈ New station</p>
            <h2 className="mt-2 text-lg font-semibold text-white">Launch a repository</h2>
            <p className="mt-1 text-sm text-slate-500">Deploy a new orbital lab for your code experiments.</p>
            <form onSubmit={handleCreate} className="mt-6 space-y-4">
              <Input label="Station name" placeholder="nebula-algorithms" value={newName} onChange={(e) => setNewName(e.target.value)} required />
              <Input label="Mission brief" placeholder="Optional — describe this station's purpose" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
              {error && (
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>
              )}
              <div className="flex justify-end gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setShowCreate(false)}>Abort</Button>
                <Button type="submit" loading={creating}>Deploy station</Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {repos.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-20 text-center" padding="lg">
          <div className="relative mb-6">
            <div className="absolute inset-0 animate-pulse-soft rounded-full bg-violet-500/20 blur-2xl" />
            <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-violet-500/30 bg-violet-500/10 text-4xl">
              🌌
            </div>
          </div>
          <h3 className="text-lg font-semibold text-white">No stations in orbit</h3>
          <p className="mt-2 max-w-sm text-sm text-slate-500">
            Launch your first repository, write Python, commit it, and receive a transmission from the AI professor.
          </p>
          <Button className="mt-8" onClick={() => setShowCreate(true)}>
            🚀 Launch first station
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {repos.map((repo) => (
            <Link key={repo.id} href={`/repos/${repo.id}`}>
              <Card hover className="group h-full border-violet-500/10">
                <div className="mb-3 flex items-start justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-500/20 bg-violet-500/10 text-lg transition-all group-hover:border-cyan-500/30 group-hover:bg-cyan-500/10 group-hover:shadow-[0_0_20px_rgba(34,211,238,0.15)]">
                    🛰️
                  </div>
                  <span className="font-mono text-xs text-violet-400/60">#{repo.id}</span>
                </div>
                <h2 className="font-semibold text-white transition-colors group-hover:text-cyan-300">
                  {repo.name}
                </h2>
                {repo.description ? (
                  <p className="mt-2 line-clamp-2 text-sm text-slate-500">{repo.description}</p>
                ) : (
                  <p className="mt-2 text-sm italic text-slate-600">No mission brief</p>
                )}
                <p className="mt-4 font-mono text-xs text-slate-600">
                  Deployed {formatRelative(repo.created_at)}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </Layout>
  );
}
