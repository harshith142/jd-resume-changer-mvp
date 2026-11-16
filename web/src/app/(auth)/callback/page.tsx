'use client';

import { Suspense } from 'react';
import { CallbackContent } from './callback-content';

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-gray-900 dark:to-gray-950 flex items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent" />
    </div>}>
      <CallbackContent />
    </Suspense>
  );
}