import { useState } from 'react';
import { submitEnquiry } from '@/lib/api';

export default function ContactForm() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await submitEnquiry(formData);
      setSuccess(true);
      setFormData({ name: '', email: '', subject: '', message: '' });
    } catch (err: any) {
      setError(err.message || 'Failed to send enquiry');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-8 text-center backdrop-blur-sm">
        <h3 className="text-xl font-bold text-indigo-400">Message Sent!</h3>
        <p className="mt-2 text-slate-400">Thank you for reaching out. We&apos;ll get back to you soon.</p>
        <button
          onClick={() => setSuccess(false)}
          className="mt-6 rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium text-white transition-all hover:bg-indigo-500 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]"
        >
          Send another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-400">Name</label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-2.5 text-slate-100 outline-none transition-all focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder:text-slate-600"
            placeholder="Your name"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-400">Email</label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="w-full rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-2.5 text-slate-100 outline-none transition-all focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder:text-slate-600"
            placeholder="your@email.com"
          />
        </div>
      </div>
      <div className="space-y-1">
        <label className="text-sm font-medium text-slate-400">Subject</label>
        <input
          type="text"
          required
          value={formData.subject}
          onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
          className="w-full rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-2.5 text-slate-100 outline-none transition-all focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder:text-slate-600"
          placeholder="What is this about?"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm font-medium text-slate-400">Message</label>
        <textarea
          required
          rows={4}
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          className="w-full rounded-lg border border-slate-800 bg-slate-900/50 px-4 py-2.5 text-slate-100 outline-none transition-all focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 placeholder:text-slate-600 resize-none"
          placeholder="Tell us what you need..."
        />
      </div>
      {error && <p className="text-sm text-red-400 bg-red-400/10 p-3 rounded-lg border border-red-400/20">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="relative w-full overflow-hidden rounded-lg bg-indigo-600 px-6 py-3 text-sm font-bold text-white transition-all hover:bg-indigo-500 hover:shadow-[0_0_25px_rgba(99,102,241,0.4)] active:scale-[0.98] disabled:opacity-50"
      >
        <span className="relative z-10">{loading ? 'Sending...' : 'Send Message'}</span>
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full hover:animate-[shimmer_2s_infinite]" />
      </button>
    </form>
  );
}
