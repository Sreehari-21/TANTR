import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode, useEffect, useState } from 'react';
import ApiStatus from '@/components/ApiStatus';
import { getMe, type User } from '@/lib/api';

export default function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!localStorage.getItem('syra_token')) return;
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, [router.pathname]);

  const nav = (
    <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="text-xl font-bold text-indigo-400">
          SYRA
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className={`${router.pathname === '/dashboard' ? 'text-indigo-400' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Dashboard
          </Link>
          {user && (
            <span className="hidden text-sm text-slate-500 sm:inline">@{user.username}</span>
          )}
          <Link
            href="/login"
            className="text-slate-400 hover:text-slate-200"
            onClick={() => localStorage.removeItem('syra_token')}
          >
            Logout
          </Link>
        </div>
      </div>
    </nav>
  );

  return (
    <div className="min-h-screen">
      <ApiStatus />
      {nav}
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
