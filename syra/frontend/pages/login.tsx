import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { ApiError, login, register } from '@/lib/api';

export default function Login() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const { access_token } = await login(username, password);
        localStorage.setItem('syra_token', access_token);
      } else {
        await register({ email, username, password, full_name: fullName || undefined });
        const { access_token } = await login(username, password);
        localStorage.setItem('syra_token', access_token);
      }
      router.replace('/dashboard');
    } catch (err: unknown) {
      if (err instanceof ApiError && err.isNetwork) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : 'Something went wrong');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-indigo-950/30 to-slate-950">
      <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900/80 p-8 shadow-xl">
        <h1 className="mb-6 text-center text-2xl font-bold text-indigo-400">SYRA</h1>
        <p className="mb-6 text-center text-slate-400">
          Learn by doing. Commit code. Get AI feedback.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                required={mode === 'register'}
              />
              <input
                type="text"
                placeholder="Full name (optional)"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </>
          )}
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            required
          />
          <input
            type="password"
            placeholder={
              mode === 'register'
                ? 'Password (12+ chars, include letter and number)'
                : 'Password'
            }
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={mode === 'register' ? 12 : undefined}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            required
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? '...' : mode === 'login' ? 'Login' : 'Register'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500">
          {mode === 'login' ? (
            <>
              Don&apos;t have an account?{' '}
              <button
                type="button"
                onClick={() => setMode('register')}
                className="text-indigo-400 hover:underline"
              >
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setMode('login')}
                className="text-indigo-400 hover:underline"
              >
                Login
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
