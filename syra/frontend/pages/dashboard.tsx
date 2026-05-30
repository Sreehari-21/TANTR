import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Layout from '@/components/Layout';
import { getRepos, createRepo, getMe } from '@/lib/api';
import type { Repo } from '@/lib/api';

export default function Dashboard() {
  const router = useRouter();
  const [repos, setRepos] = useState<Repo[]>([]);
  const [user, setUser] = useState<{ username: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('syra_token');
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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create repo');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="text-slate-500">Loading...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">
          Repositories {user && <span className="text-slate-500">· {user.username}</span>}
        </h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          New repository
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-6 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
          <input
            type="text"
            placeholder="Repository name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="mb-2 w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100"
            required
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="mb-2 w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100"
          />
          {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={creating} className="rounded bg-indigo-600 px-4 py-1 text-sm text-white">
              Create
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="rounded bg-slate-700 px-4 py-1 text-sm">
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {repos.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-slate-500">
            No repositories yet. Create one to get started.
          </div>
        ) : (
          repos.map((repo) => (
            <Link
              key={repo.id}
              href={`/repos/${repo.id}`}
              className="block rounded-lg border border-slate-800 bg-slate-900/50 p-4 transition hover:border-indigo-500/50 hover:bg-slate-900"
            >
              <h2 className="font-semibold text-indigo-400">{repo.name}</h2>
              {repo.description && <p className="mt-1 text-sm text-slate-500">{repo.description}</p>}
            </Link>
          ))
        )}
      </div>
    </Layout>
  );
}
