'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const error = searchParams.get('error');
  const accessToken = searchParams.get('access_token');
  const refreshToken = searchParams.get('refresh_token');

  useEffect(() => {
    if (error) {
      router.push(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    if (accessToken && refreshToken) {
      localStorage.setItem('backend-jwt-token', accessToken);
      localStorage.setItem('backend-refresh-token', refreshToken);
      const destination = searchParams.get('callbackUrl') || '/dashboard';
      router.push(destination.startsWith('/') ? destination : `/${destination}`);
      return;
    }

    router.push('/login?error=Authentication');
  }, [router, searchParams, error, accessToken, refreshToken]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-gray-900 dark:to-gray-950 flex items-center justify-center px-4">
      <div className="text-center">
        <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mx-auto mb-4">
          <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Completing sign in...</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Please wait while we redirect you.</p>
      </div>
    </div>
  );
}