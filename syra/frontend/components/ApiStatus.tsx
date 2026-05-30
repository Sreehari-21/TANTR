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
      className="border-b border-amber-500/40 bg-amber-950/90 px-4 py-2 text-center text-sm text-amber-100"
    >
      API offline — start the backend with{' '}
      <code className="rounded bg-amber-900/60 px-1.5 py-0.5 font-mono text-xs">
        ./scripts/run-backend.sh
      </code>{' '}
      (expected at {API_BASE})
    </div>
  );
}
