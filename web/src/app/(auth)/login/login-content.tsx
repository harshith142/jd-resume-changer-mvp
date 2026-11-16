'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FileText, Loader2, Mail, Lock } from 'lucide-react';
import Link from 'next/link';

export function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const error = searchParams.get('error');
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
      const endpoint = isRegister ? `${apiBaseUrl}/api/v1/auth/register` : `${apiBaseUrl}/api/v1/auth/login`;
      const body = isRegister ? { name, email, password } : { email, password };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const serverMessage = typeof data?.detail === 'string' ? data.detail : 'Authentication failed';
        throw new Error(serverMessage);
      }

      if (data?.tokens?.access_token && data?.tokens?.refresh_token) {
        localStorage.setItem('backend-jwt-token', data.tokens.access_token);
        localStorage.setItem('backend-refresh-token', data.tokens.refresh_token);
        router.push('/dashboard');
        return;
      }

      throw new Error('No auth tokens returned');
    } catch (err) {
      console.error('Login error:', err);
      const message = err instanceof Error && err.message ? err.message : 'Authentication failed';
      setMessage(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-gray-900 dark:to-gray-950 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <FileText className="h-10 w-10 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900 dark:text-white">JD Resume Changer</span>
          </Link>
        </div>

        {/* Card */}
        <div className="card p-8">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {isRegister ? 'Create account' : 'Welcome back'}
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              {isRegister ? 'Create your account to get started.' : 'Sign in to tailor your resume with AI'}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {message && (
            <div className="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 text-sm">
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Full name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2.5 text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                  placeholder="Jane Doe"
                  required={isRegister}
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Email</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 bg-white py-2.5 pl-9 pr-3 text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1">Password</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-lg border border-gray-200 bg-white py-2.5 pl-9 pr-3 text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                  placeholder="••••••••"
                  minLength={6}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : isRegister ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600 dark:text-gray-300">
            <button
              type="button"
              onClick={() => setIsRegister((prev) => !prev)}
              className="text-primary-600 hover:underline font-medium"
            >
              {isRegister ? 'Already have an account? Sign in' : 'Need an account? Create one'}
            </button>
          </div>

          <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>By continuing, you agree to our </p>
            <Link href="/terms" className="text-primary-600 hover:underline">Terms of Service</Link>
            <p> and </p>
            <Link href="/privacy" className="text-primary-600 hover:underline">Privacy Policy</Link>
          </div>
        </div>
      </div>
    </div>
  );
}