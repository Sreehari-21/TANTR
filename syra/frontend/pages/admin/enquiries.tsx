import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { getAdminEnquiries, getMe } from '@/lib/api';
import type { Enquiry } from '@/lib/api';

export default function AdminEnquiriesPage() {
  const router = useRouter();
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('syra_token');
    if (!token) {
      router.replace('/login');
      return;
    }

    getMe().then((user) => {
      if (!user.is_admin) {
        router.replace('/dashboard');
        return;
      }
      return getAdminEnquiries();
    }).then((data) => {
      if (data) setEnquiries(data);
    }).catch((err) => {
      setError('Failed to load enquiries or unauthorized');
    }).finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <Layout>
        <div className="flex min-h-[400px] items-center justify-center text-slate-500">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-100">Admin Enquiries</h1>
        <p className="mt-2 text-slate-400">View and manage form submissions from users.</p>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-red-400">
          {error}
        </div>
      ) : enquiries.length === 0 ? (
        <div className="flex min-h-[200px] items-center justify-center rounded-xl border border-dashed border-slate-800 text-slate-500">
          No enquiries found.
        </div>
      ) : (
        <div className="grid gap-4">
          {enquiries.map((e) => (
            <div
              key={e.id}
              className="group rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition-all hover:bg-slate-900 hover:border-indigo-500/30"
            >
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-200">{e.subject}</h3>
                  <div className="mt-1 flex gap-3 text-sm text-slate-500">
                    <span className="text-indigo-400">{e.name}</span>
                    <span>&bull;</span>
                    <span>{e.email}</span>
                  </div>
                </div>
                <div className="text-xs text-slate-600">
                  {new Date(e.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="rounded-lg bg-slate-950/50 p-4 text-slate-300 shadow-inner">
                {e.message}
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
