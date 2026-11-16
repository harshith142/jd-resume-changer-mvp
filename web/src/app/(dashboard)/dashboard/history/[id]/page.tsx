'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Loader2,
  FileText,
  Briefcase,
  Download,
  ArrowLeft,
  Trash2,
  TrendingUp,
  CheckCircle,
  XCircle,
  Zap,
  Brain,
  Copy,
  Eye,
  AlertCircle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { generatedResumeApi, GeneratedResume } from '@/lib/api';
import { toast } from 'sonner';

export default function HistoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [generation, setGeneration] = useState<GeneratedResume | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'preview' | 'latex'>('preview');

  useEffect(() => {
    const fetchGeneration = async () => {
      try {
        setLoading(true);
        const response = await generatedResumeApi.get(id);
        setGeneration(response.data);
      } catch (error) {
        toast.error('Failed to load generation');
        router.push('/dashboard/history');
      } finally {
        setLoading(false);
      }
    };
    fetchGeneration();
  }, [id, router]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this generation? This action cannot be undone.')) return;

    setDeleting(true);
    try {
      await generatedResumeApi.delete(id);
      toast.success('Generation deleted');
      router.push('/dashboard/history');
    } catch (error) {
      toast.error('Failed to delete generation');
    } finally {
      setDeleting(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!generation) return;
    try {
      const response = await generatedResumeApi.downloadPdf(id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const title = generation.jd_title ?? generation.job_description_title ?? 'untitled';
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_tailored_resume.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download PDF');
    }
  };

  const handleDownloadTex = async () => {
    if (!generation) return;
    try {
      const response = await generatedResumeApi.downloadTex(id);
      const blob = new Blob([response.data], { type: 'text/x-tex' });
      const url = URL.createObjectURL(blob);
      const title = generation.jd_title ?? generation.job_description_title ?? 'untitled';
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_tailored_resume.tex`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download LaTeX');
    }
  };

  const handleCopyLatex = () => {
    if (generation?.tailored_latex) {
      navigator.clipboard.writeText(generation.tailored_latex);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const statusColors = {
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    processing: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    pending: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
  };

  const statusIcons = {
    completed: CheckCircle,
    processing: Loader2,
    failed: XCircle,
    pending: Zap,
  };

  const matchedKeywords = generation?.keyword_match?.matched_keywords ?? [];
  const missingKeywords = generation?.keyword_match?.missing_keywords ?? [];

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        </div>
        <div className="card p-6">
          <div className="h-60 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  if (!generation) {
    return (
      <div className="max-w-5xl mx-auto">
        <div className="card p-12 text-center">
          <FileText className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Generation not found</h3>
          <Link href="/dashboard/history" className="text-primary-600 hover:underline">Back to history</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Link
            href="/dashboard/history"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to History
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{generation.jd_title ?? generation.job_description_title ?? 'Untitled'}</h1>
          <p className="mt-1 text-gray-500 dark:text-gray-400">
            Tailored from: <span className="font-medium text-gray-700 dark:text-gray-300">{generation.master_resume_title}</span>
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {generation.status === 'completed' && (
            <>
              <button onClick={handleDownloadPdf} className="btn-outline" title="Download PDF">
                <Download className="h-4 w-4" />
              </button>
              <button onClick={handleDownloadTex} className="btn-outline" title="Download LaTeX">
                <FileText className="h-4 w-4" />
              </button>
            </>
          )}
          <button onClick={handleCopyLatex} className="btn-outline" title="Copy LaTeX">
            {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="btn-outline text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-200 dark:border-red-800"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Status & Metrics */}
      <div className="card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className={`px-4 py-2 rounded-full ${statusColors[generation.status] ?? statusColors.pending}`}>
              {(() => {
                const StatusIcon = statusIcons[generation.status];
                return (
                  <span className="flex items-center gap-2 font-medium">
                    <StatusIcon className="h-4 w-4" />
                    {generation.status.charAt(0).toUpperCase() + generation.status.slice(1)}
                  </span>
                );
              })()}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Created {formatDistanceToNow(new Date(generation.created_at), { addSuffix: true })}
              {generation.updated_at && generation.updated_at !== generation.created_at && (
                <> • Updated {formatDistanceToNow(new Date(generation.updated_at), { addSuffix: true })}</>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            {generation.ats_score !== null && (
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800 min-w-[100px]">
                <div className="text-3xl font-bold text-green-700 dark:text-green-300">{generation.ats_score}%</div>
                <div className="text-xs text-green-600 dark:text-green-400">ATS Score</div>
              </div>
            )}
            {generation.keyword_match && (
              <div className="text-center p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg border border-primary-200 dark:border-primary-800 min-w-[100px]">
                <div className="text-3xl font-bold text-primary-700 dark:text-primary-300">{generation.keyword_match.match_percentage}%</div>
                <div className="text-xs text-primary-600 dark:text-primary-400">Keyword Match</div>
              </div>
            )}
            {generation.generation_time_ms && (
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 min-w-[100px]">
                <div className="text-3xl font-bold text-gray-700 dark:text-gray-300">{Math.round(generation.generation_time_ms / 1000)}s</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">Generation Time</div>
              </div>
            )}
          </div>
        </div>

        {generation.error_message && generation.status === 'failed' && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-800 dark:text-red-200">Generation Failed</p>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{generation.error_message}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Keyword Match Details */}
      {generation.keyword_match && generation.status === 'completed' && (
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Keyword Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-green-700 dark:text-green-300 mb-3 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" /> Matched Keywords ({matchedKeywords.length})
              </h4>
              <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto">
                {matchedKeywords.map((kw, i) => (
                  <span key={i} className="px-3 py-1 text-sm bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h4 className="font-medium text-red-700 dark:text-red-300 mb-3 flex items-center gap-1">
                <XCircle className="h-4 w-4" /> Missing Keywords ({missingKeywords.length})
              </h4>
              <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto">
                {missingKeywords.map((kw, i) => (
                  <span key={i} className="px-3 py-1 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LaTeX Viewer / Preview */}
      {generation.status === 'completed' && (
        <div className="card">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Tailored LaTeX</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode('preview')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  viewMode === 'preview'
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                Preview
              </button>
              <button
                onClick={() => setViewMode('latex')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  viewMode === 'latex'
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                LaTeX Source
              </button>
              <button onClick={handleCopyLatex} className="btn-outline text-sm">
                {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              </button>
              <button onClick={handleDownloadTex} className="btn-outline text-sm">
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="p-4">
            {viewMode === 'latex' ? (
              <pre className="bg-gray-950 text-gray-100 p-4 rounded-lg overflow-x-auto max-h-[600px] font-mono text-sm">
                <code>{generation.tailored_latex}</code>
              </pre>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none p-4 bg-white dark:bg-gray-900">
                <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">
                  {generation.tailored_latex}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Generation Steps */}
      {generation.status === 'completed' && (
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Generation Pipeline</h3>
          <div className="space-y-3">
            {[
              { label: 'Parse Job Description', icon: Brain },
              { label: 'Parse Master Resume', icon: FileText },
              { label: 'Match Skills & Experience', icon: Zap },
              { label: 'Generate Tailored LaTeX', icon: Brain },
              { label: 'Sanitize & Validate LaTeX', icon: CheckCircle },
              { label: 'Compile PDF', icon: FileText },
              { label: 'Calculate ATS Score', icon: TrendingUp },
            ].map((step, index) => (
              <div key={step.label} className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                </div>
                <span className="text-gray-700 dark:text-gray-300">{step.label}</span>
                <span className="text-xs text-gray-400 ml-auto">Completed</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Actions</h3>
        <div className="flex flex-wrap gap-4">
          <Link href="/dashboard/generate" className="btn-primary">
            Generate Another
          </Link>
          <Link href="/dashboard/resumes" className="btn-outline">
            View Resumes
          </Link>
          <Link href="/dashboard/job-descriptions" className="btn-outline">
            View Job Descriptions
          </Link>
        </div>
      </div>
    </div>
  );
}