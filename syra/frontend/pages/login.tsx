import { useState } from 'react';
import { useRouter } from 'next/router';
import { ApiError, login, register } from '@/lib/api';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Card from '@/components/ui/Card';
import SpaceBackground from '@/components/SpaceBackground';

const FEATURES = [
  {
    icon: '🛸',
    title: 'Launch commits',
    desc: 'Write Python in a stellar editor and push code into orbit.',
  },
  {
    icon: '🌌',
    title: 'AI professor',
    desc: 'Every transmission gets scanned, graded, and decoded with feedback.',
  },
  {
    icon: '🪐',
    title: 'Track your trajectory',
    desc: 'Monitor scores across quality, efficiency, docs, and consistency.',
  },
];

function PlanetHero() {
  return (
    <div className="relative mx-auto flex h-48 w-48 items-center justify-center">
      {/* Orbit ring */}
      <div className="orbit-ring absolute h-44 w-44 animate-orbit border-dashed" />
      <div className="orbit-ring absolute h-36 w-36 animate-orbit border-violet-400/10" style={{ animationDirection: 'reverse', animationDuration: '15s' }} />
      {/* Planet */}
      <div className="relative h-24 w-24 animate-float rounded-full bg-gradient-to-br from-violet-600 via-indigo-600 to-cyan-500 shadow-[0_0_60px_rgba(139,92,246,0.5)]">
        <div className="absolute inset-2 rounded-full bg-gradient-to-br from-violet-400/30 to-transparent" />
        <div className="absolute -right-2 top-4 h-4 w-4 rounded-full bg-cyan-400/80 shadow-[0_0_12px_rgba(34,211,238,0.8)]" />
      </div>
      {/* Satellite */}
      <div className="absolute right-0 top-0 h-3 w-3 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(34,211,238,1)] animate-pulse-soft" />
    </div>
  );
}

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
    <div className="relative flex min-h-screen">
      <SpaceBackground />

      {/* Hero panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden border-r border-violet-500/10 p-12 lg:flex">
        <div className="relative">
          <p className="mb-4 font-mono text-xs uppercase tracking-[0.3em] text-cyan-400/80">
            ◈ Deep space learning platform
          </p>
          <h1 className="text-4xl font-bold leading-tight tracking-tight text-white">
            Code among the
            <br />
            <span className="cosmic-text">stars.</span>
          </h1>
          <p className="mt-4 max-w-md text-lg text-slate-400">
            SYRA is your AI mission control — commit code, receive transmissions from your professor, and chart your course through the cosmos.
          </p>
        </div>

        <PlanetHero />

        <div className="relative space-y-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="flex gap-4 rounded-xl border border-violet-500/10 bg-violet-500/5 p-4 backdrop-blur-sm transition-colors hover:border-violet-500/20 hover:bg-violet-500/10"
            >
              <span className="text-2xl">{f.icon}</span>
              <div>
                <h3 className="font-semibold text-slate-200">{f.title}</h3>
                <p className="text-sm text-slate-500">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Auth form */}
      <div className="relative flex flex-1 items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md animate-slide-up">
          <div className="mb-8 text-center lg:hidden">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-cyan-500 text-xl font-bold text-white shadow-[0_0_30px_rgba(139,92,246,0.4)]">
              ✦
            </div>
            <h1 className="text-2xl font-bold cosmic-text">SYRA</h1>
            <p className="mt-1 text-xs text-slate-500">Deep space learning</p>
          </div>

          <Card padding="lg">
            <p className="font-mono text-xs uppercase tracking-widest text-cyan-400/70">
              {mode === 'login' ? '◈ Docking sequence' : '◈ New crew member'}
            </p>
            <h2 className="mt-2 text-xl font-semibold text-white">
              {mode === 'login' ? 'Welcome back, explorer' : 'Join the mission'}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {mode === 'login' ? 'Authenticate to enter mission control' : 'Register to begin your voyage'}
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {mode === 'register' && (
                <>
                  <Input label="Email" type="email" placeholder="you@university.edu" value={email} onChange={(e) => setEmail(e.target.value)} required />
                  <Input label="Full name" type="text" placeholder="Optional" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </>
              )}
              <Input label="Username" type="text" placeholder="stellar_coder" value={username} onChange={(e) => setUsername(e.target.value)} required />
              <Input
                label="Password"
                type="password"
                placeholder={mode === 'register' ? '12+ chars, letter and number' : '••••••••••••'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={mode === 'register' ? 12 : undefined}
                required
              />
              {error && (
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
                  {error}
                </div>
              )}
              <Button type="submit" loading={loading} className="w-full">
                {mode === 'login' ? '🚀 Launch session' : '🌟 Begin voyage'}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-500">
              {mode === 'login' ? (
                <>
                  New explorer?{' '}
                  <button type="button" onClick={() => setMode('register')} className="font-medium text-cyan-400 hover:text-cyan-300">
                    Join the mission
                  </button>
                </>
              ) : (
                <>
                  Already aboard?{' '}
                  <button type="button" onClick={() => setMode('login')} className="font-medium text-cyan-400 hover:text-cyan-300">
                    Dock in
                  </button>
                </>
              )}
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
