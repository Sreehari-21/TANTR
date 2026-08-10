import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import Card from '@/components/ui/Card';
import Spinner from '@/components/ui/Spinner';
import { getAdminEnquiries, getMe } from '@/lib/api';
import type { Enquiry } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function AdminEnquiriesPage() {
  const router = useRouter();
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('tantr_token');
    if (!token) {
      router.replace('/login');
      return;
    }

    getMe()
      .then((user) => {
        if (!user.is_admin) {
          router.replace('/dashboard');
          return;
        }
        return getAdminEnquiries();
      })
      .then((data) => {
        if (data) setEnquiries(data);
      })
      .catch(() => setError('Failed to load enquiries or unauthorized'))
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) {
    return (
      <Layout>
        <Spinner className="min-h-[50vh]" />
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-8">
        <p className="text-sm font-medium text-indigo-400">Admin</p>
        <h1 className="page-title">Enquiries</h1>
        <p className="page-subtitle">Contact form submissions from users.</p>
      </div>

      {error ? (
        <Card className="border-rose-500/20 text-rose-300">{error}</Card>
      ) : enquiries.length === 0 ? (
        <Card className="py-16 text-center text-slate-500" padding="lg">
          No enquiries yet.
        </Card>
      ) : (
        <div className="grid gap-4">
          {enquiries.map((e) => (
            <Card key={e.id} hover>
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-slate-100">{e.subject}</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    <span className="text-indigo-400">{e.name}</span> · {e.email}
                  </p>
                </div>
                <time className="shrink-0 text-xs text-slate-600">{formatDate(e.created_at)}</time>
              </div>
              <p className="rounded-xl bg-slate-950/50 p-4 text-sm leading-relaxed text-slate-300">
                {e.message}
              </p>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
