'use client';

import { useSession } from 'next-auth/react';
import Link from 'next/link';
import {
  FileText,
  Briefcase,
  History,
  Plus,
  TrendingUp,
  ArrowRight,
  CheckCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  href: string;
  description: string;
}

function StatCard({ title, value, icon, href, description }: StatCardProps) {
  return (
    <Link
      href={href}
      className="card p-6 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
          <p className="mt-1 text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
        <div className="h-12 w-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600">
          {icon}
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span className="text-sm text-gray-500 dark:text-gray-400">View all</span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
      </div>
    </Link>
  );
}

interface RecentItemProps {
  type: 'resume' | 'jd' | 'generated';
  title: string;
  subtitle: string;
  date: string;
  status?: 'completed' | 'processing' | 'failed';
  href: string;
}

function RecentItem({ type, title, subtitle, date, status, href }: RecentItemProps) {
  const icons = {
    resume: FileText,
    jd: Briefcase,
    generated: History,
  };
  const Icon = icons[type];

  const statusConfig = {
    completed: { icon: CheckCircle, color: 'text-green-500', label: 'Completed' },
    processing: { icon: Clock, color: 'text-yellow-500 animate-spin', label: 'Processing' },
    failed: { icon: AlertTriangle, color: 'text-red-500', label: 'Failed' },
  };

  // Render status badge outside JSX to avoid parsing issues
  const statusBadge = status && statusConfig[status] ? (
    (() => {
      const StatusIcon = statusConfig[status].icon;
      return (
        <span className={`flex items-center gap-1 text-xs font-medium ${statusConfig[status].color}`}>
          <StatusIcon className="h-3 w-3" />
          {statusConfig[status].label}
        </span>
      );
    })()
  ) : null;

  return (
    <Link href={href} className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-lg transition-colors">
      <div className="h-10 w-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 flex-shrink-0">
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 dark:text-white truncate">{title}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        {statusBadge}
        <span className="text-xs text-gray-400 whitespace-nowrap">{formatDistanceToNow(new Date(date), { addSuffix: true })}</span>
        <ArrowRight className="h-4 w-4 text-gray-400" />
      </div>
    </Link>
  );
}

export default function DashboardPage() {
  const { data: session } = useSession();

  // Mock data - replace with actual API calls
  const stats = [
    {
      title: 'Master Resumes',
      value: 3,
      icon: <FileText className="h-6 w-6" />,
      href: '/dashboard/resumes',
      description: 'Ready to tailor',
    },
    {
      title: 'Job Descriptions',
      value: 12,
      icon: <Briefcase className="h-6 w-6" />,
      href: '/dashboard/job-descriptions',
      description: 'Saved for matching',
    },
    {
      title: 'Generated Resumes',
      value: 8,
      icon: <History className="h-6 w-6" />,
      href: '/dashboard/history',
      description: 'ATS optimized',
    },
    {
      title: 'Avg ATS Score',
      value: '87%',
      icon: <TrendingUp className="h-6 w-6" />,
      href: '/dashboard/history',
      description: 'Across all generations',
    },
  ];

  const recentResumes = [
    { id: '1', title: 'Senior Software Engineer Resume', subtitle: 'Default • Updated 2 days ago', date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), href: '/dashboard/resumes/1' },
    { id: '2', title: 'Full Stack Developer Profile', subtitle: 'Backend focused • Updated 1 week ago', date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), href: '/dashboard/resumes/2' },
  ];

  const recentJDs = [
    { id: '1', title: 'Staff Engineer at TechCorp', subtitle: 'Remote • $180k-250k • Posted 3 days ago', date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), href: '/dashboard/job-descriptions/1' },
    { id: '2', title: 'Principal Engineer at StartupXYZ', subtitle: 'SF Bay Area • $200k-300k • Posted 1 week ago', date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), href: '/dashboard/job-descriptions/2' },
  ];

  const recentGenerated = [
    { id: '1', title: 'Staff Engineer at TechCorp', subtitle: 'Senior Software Engineer Resume • ATS: 92%', date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), status: 'completed' as const, href: '/dashboard/history/1' },
    { id: '2', title: 'Principal Engineer at StartupXYZ', subtitle: 'Full Stack Developer Profile • ATS: 85%', date: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(), status: 'completed' as const, href: '/dashboard/history/2' },
    { id: '3', title: 'Tech Lead at BigCorp', subtitle: 'Senior Software Engineer Resume • ATS: 78%', date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), status: 'completed' as const, href: '/dashboard/history/3' },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {session?.user?.name?.split(' ')[0] || 'there'}!
        </h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Here's an overview of your resume tailoring activity
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <StatCard key={i} {...stat} />
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Link
          href="/dashboard/resumes/new"
          className="card p-6 hover:shadow-md transition-shadow border-2 border-dashed border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mx-auto mb-4">
            <Plus className="h-8 w-8 text-primary-600" />
          </div>
          <h3 className="text-lg font-semibold text-center text-gray-900 dark:text-white mb-2">Add Master Resume</h3>
          <p className="text-sm text-center text-gray-500 dark:text-gray-400">Upload or paste your base resume in LaTeX format</p>
        </Link>

        <Link
          href="/dashboard/job-descriptions/new"
          className="card p-6 hover:shadow-md transition-shadow border-2 border-dashed border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center justify-center h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 mx-auto mb-4">
            <Plus className="h-8 w-8 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-center text-gray-900 dark:text-white mb-2">Add Job Description</h3>
          <p className="text-sm text-center text-gray-500 dark:text-gray-400">Paste JD text or upload PDF/DOCX/TXT file</p>
        </Link>

        <Link
          href="/dashboard/generate"
          className="card p-6 hover:shadow-md transition-shadow bg-primary-600 text-white"
        >
          <div className="flex items-center justify-center h-16 w-16 rounded-full bg-primary-500/20 mx-auto mb-4">
            <TrendingUp className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-center mb-2">Generate Tailored Resume</h3>
          <p className="text-sm text-center text-primary-100">Match your resume to a job description with AI</p>
        </Link>
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Resumes */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Resumes</h3>
            <Link href="/dashboard/resumes" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {recentResumes.map((item) => (
              <RecentItem
                key={item.id}
                type="resume"
                title={item.title}
                subtitle={item.subtitle}
                date={item.date}
                href={item.href}
              />
            ))}
            {recentResumes.length === 0 && (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <FileText className="h-12 w-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                <p>No resumes yet</p>
                <Link href="/dashboard/resumes/new" className="text-primary-600 hover:underline text-sm mt-2 inline-block">Add one</Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Job Descriptions */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Job Descriptions</h3>
            <Link href="/dashboard/job-descriptions" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {recentJDs.map((item) => (
              <RecentItem
                key={item.id}
                type="jd"
                title={item.title}
                subtitle={item.subtitle}
                date={item.date}
                href={item.href}
              />
            ))}
            {recentJDs.length === 0 && (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <Briefcase className="h-12 w-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                <p>No job descriptions yet</p>
                <Link href="/dashboard/job-descriptions/new" className="text-primary-600 hover:underline text-sm mt-2 inline-block">Add one</Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Generated */}
        <div className="card">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Generations</h3>
            <Link href="/dashboard/history" className="text-sm text-primary-600 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {recentGenerated.map((item) => (
              <RecentItem
                key={item.id}
                type="generated"
                title={item.title}
                subtitle={item.subtitle}
                date={item.date}
                status={item.status}
                href={item.href}
              />
            ))}
            {recentGenerated.length === 0 && (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                <History className="h-12 w-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                <p>No generations yet</p>
                <Link href="/dashboard/generate" className="text-primary-600 hover:underline text-sm mt-2 inline-block">Generate one</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}