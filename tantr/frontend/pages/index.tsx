import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Spinner from '@/components/ui/Spinner';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('tantr_token');
    if (token) router.replace('/dashboard');
    else router.replace('/login');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Spinner label="Loading TANTR..." />
    </div>
  );
}
