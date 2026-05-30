import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('syra_token');
    if (token) router.replace('/dashboard');
    else router.replace('/login');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="animate-pulse text-slate-500">Loading...</div>
    </div>
  );
}
