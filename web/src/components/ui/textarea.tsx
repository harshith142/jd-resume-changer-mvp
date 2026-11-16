'use client';

import { TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className='w-full'>
        <textarea
          className={cn(
            'flex w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-900 dark:text-white dark:placeholder:text-gray-400',
            error && 'border-red-500 focus-visible:ring-red-500',
            className
          )}
          ref={ref}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? 'error-message' : undefined}
          {...props}
        />
        {error && (
          <p id='error-message' className='mt-1 text-sm text-red-500' role='alert'>
            {error}
          </p>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

export { Textarea };
