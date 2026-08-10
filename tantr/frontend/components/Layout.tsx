import Link from 'next/link';
import { useRouter } from 'next/router';
import { ReactNode, useEffect, useState } from 'react';
import ApiStatus from '@/components/ApiStatus';
import SpaceBackground from '@/components/SpaceBackground';
import { getMe, type User } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function Layout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (!localStorage.getItem('tantr_token')) return;
    getMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, [router.pathname]);

  const links = [
    { href: '/dashboard', label: 'Mission Control' },
    ...(user?.is_admin ? [{ href: '/admin/enquiries', label: 'Comms' }] : []),
  ];

  return (
    <div className="relative flex min-h-screen flex-col">
      <SpaceBackground />
      <ApiStatus />

      <nav className="sticky top-0 z-40 border-b border-violet-500/10 bg-[#030014]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/dashboard" className="group flex items-center gap-2.5">
            <div className="relative flex h-9 w-9 items-center justify-center">
              <div className="absolute inset-0 animate-glow-pulse rounded-xl bg-gradient-to-br from-violet-600 to-cyan-600 opacity-60 blur-sm" />
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-cyan-500 text-sm font-bold text-white transition-transform group-hover:scale-105">
                ✦
              </div>
            </div>
            <span className="text-lg font-bold tracking-widest text-white">
              TANTR
            </span>
          </Link>

          <div className="flex items-center gap-1 sm:gap-2">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'rounded-lg px-3 py-2 text-sm font-medium transition-all',
                  router.pathname === link.href || router.pathname.startsWith(link.href + '/')
                    ? 'bg-violet-500/15 text-cyan-300 shadow-[0_0_12px_rgba(34,211,238,0.1)]'
                    : 'text-slate-400 hover:bg-violet-500/10 hover:text-violet-200'
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-3">
            {user && (
              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-8 w-8 items-center justify-center rounded-full border border-violet-500/30 bg-gradient-to-br from-violet-600/30 to-cyan-600/20 text-xs font-semibold text-cyan-200">
                  {user.username[0]?.toUpperCase()}
                </div>
                <span className="text-sm text-slate-500">@{user.username}</span>
              </div>
            )}
            <button
              type="button"
              onClick={() => {
                localStorage.removeItem('tantr_token');
                router.push('/login');
              }}
              className="rounded-lg px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-violet-500/10 hover:text-slate-300"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>

      <main className="relative mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 animate-fade-in">
        {children}
      </main>

      <footer className="relative border-t border-violet-500/10 py-6 text-center text-xs text-slate-600">
        <span className="cosmic-text font-medium">TANTR</span>
        <span className="text-slate-600"> — navigating the code cosmos</span>
      </footer>
    </div>
  );
}
