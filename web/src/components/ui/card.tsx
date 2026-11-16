'use client';

import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {}

const Card = forwardRef<HTMLDivElement, CardProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900', className)} {...props} />
));
Card.displayName = 'Card';

const CardHeader = forwardRef<HTMLDivElement, CardProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('px-6 py-4 border-b border-gray-200 dark:border-gray-700', className)} {...props} />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(({ className, ...props }, ref) => (
  <h3 ref={ref} className={cn('text-lg font-semibold text-gray-900 dark:text-white', className)} {...props} />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(({ className, ...props }, ref) => (
  <p ref={ref} className={cn('mt-1 text-sm text-gray-500 dark:text-gray-400', className)} {...props} />
));
CardDescription.displayName = 'CardDescription';

const CardContent = forwardRef<HTMLDivElement, CardProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('p-6', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = forwardRef<HTMLDivElement, CardProps>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('px-6 py-4 border-t border-gray-200 dark:border-gray-700', className)} {...props} />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
