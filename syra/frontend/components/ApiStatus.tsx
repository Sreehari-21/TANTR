import { useEffect, useState } from 'react';
import { API_BASE, checkApiHealth } from '@/lib/api';

const POLL_MS = 15000;

export default function ApiStatus() {
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    const ping = async () => {
      const ok = await checkApiHealth();
      if (!cancelled) setOnline(ok);
    };
    ping();
    const id = setInterval(ping, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (online !== false) return null;

  return (
    <div
      role="alert"
      className="relative z-50 flex items-center justify-center gap-2 border-b border-amber-500/30 bg-amber-950/90 px-4 py-2.5 text-center text-sm text-amber-100"
    >
      <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]" />
      Uplink offline — run{' '}
      <code className="rounded-md bg-amber-900/50 px-1.5 py-0.5 font-mono text-xs">
        ./scripts/run-backend.sh
      </code>{' '}
      <span className="hidden sm:inline">(expected at {API_BASE})</span>
    </div>
  );
}
