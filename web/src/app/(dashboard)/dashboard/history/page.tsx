'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Loader2, FileText, Briefcase, Download, Eye, Trash2, TrendingUp, Filter, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { generatedResumeApi, GeneratedResume, GeneratedResumeListItem, PaginatedResponse } from '@/lib/api';
import { toast } from 'sonner';

export default function HistoryPage() {
  const [history, setHistory] = useState<GeneratedResumeListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const safeHistory = Array.isArray(history) ? history : [];

  const fetchHistory = async (pageNum = 1) => {
    try {
      setLoading(true);
      const params: Record<string, string | number> = { page: pageNum, size: 20 };
      if (search) params.search = search;
      if (statusFilter !== 'all') params.status = statusFilter;

      const response = await generatedResumeApi.list(params);
      const data: PaginatedResponse<GeneratedResumeListItem> = response.data ?? { items: [], total: 0, page: pageNum, size: 20, pages: 1 };
      setHistory(Array.isArray(data.items) ? data.items : []);
      setTotalPages(data.pages ?? 1);
      setTotal(data.total ?? 0);
      setPage(data.page ?? pageNum);
    } catch (error) {
      toast.error('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this generation? This action cannot be undone.')) return;

    setDeletingId(id);
    try {
      await generatedResumeApi.delete(id);
      toast.success('Generation deleted');
      fetchHistory(page);
    } catch (error) {
      toast.error('Failed to delete generation');
    } finally {
      setDeletingId(null);
    }
  };

  const handleDownloadPdf = async (id: string, title: string) => {
    try {
      const response = await generatedResumeApi.downloadPdf(id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_tailored_resume.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download PDF');
    }
  };

  const handleDownloadTex = async (id: string, title: string) => {
    try {
      const response = await generatedResumeApi.downloadTex(id);
      const blob = new Blob([response.data], { type: 'text/x-tex' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_tailored_resume.tex`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download LaTeX');
    }
  };

  useEffect(() => {
    fetchHistory(1);
  }, [search, statusFilter]);

  const statusColors = {
    completed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    processing: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300',
    failed: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    pending: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Generation History</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">View and manage your tailored resume generations</p>
        </div>
        <Link href="/dashboard/generate" className="btn-primary">
          <TrendingUp className="h-4 w-4" />
          Generate New
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <form className="flex flex-col sm:flex-row gap-4" onSubmit={(e) => e.preventDefault()}>
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by resume title, JD title..."
              className="input pl-10"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
        </form>
      </div>

      {/* History List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="flex items-start gap-4">
                <div className="h-12 w-12 rounded-lg bg-gray-200 dark:bg-gray-700" />
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : safeHistory.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No generations yet</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">Generate your first tailored resume to see history here</p>
          <Link href="/dashboard/generate" className="btn-primary inline-flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Generate Resume
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {safeHistory.map((item) => {
              const status = item.status ?? 'pending';
              const safeStatusLabel = status.charAt(0).toUpperCase() + status.slice(1);

              return (
                <div key={item.id} className="card p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white truncate">{item.job_description_title ?? 'Untitled'}</h3>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${statusColors[status] ?? statusColors.pending}`}>
                          {safeStatusLabel}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                        Based on: <span className="font-medium text-gray-700 dark:text-gray-300">{item.master_resume_name ?? 'Untitled'}</span>
                      </p>
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        <span>{formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}</span>
                        {item.ats_score !== null && (
                          <span className="flex items-center gap-1 text-green-600 dark:text-green-400 font-medium">
                            <TrendingUp className="h-3.5 w-3.5" />
                            ATS: {item.ats_score}%
                          </span>
                        )}
                        {item.keyword_match && (
                          <span className="flex items-center gap-1 text-primary-600 dark:text-primary-400 font-medium">
                            Keyword Match: {item.keyword_match.match_percentage}%
                          </span>
                        )}
                        {item.generation_time_ms && (
                          <span>⏱ {Math.round(item.generation_time_ms / 1000)}s</span>
                        )}
                      </div>
                      {item.error_message && item.status === 'failed' && (
                        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{item.error_message}</p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.status === 'completed' && (
                        <>
                          <button
                            onClick={() => handleDownloadPdf(item.id, item.job_description_title ?? 'untitled')}
                            className="btn-outline text-sm"
                            title="Download PDF"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDownloadTex(item.id, item.job_description_title ?? 'untitled')}
                            className="btn-outline text-sm"
                            title="Download LaTeX"
                          >
                            <FileText className="h-4 w-4" />
                          </button>
                        </>
                      )}
                      <Link
                        href={`/dashboard/history/${item.id}`}
                        className="btn-outline text-sm"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={() => handleDelete(item.id)}
                        disabled={deletingId === item.id}
                        className="btn-outline text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-200 dark:border-red-800"
                      >
                        {deletingId === item.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => fetchHistory(page - 1)}
                disabled={page <= 1}
                className="btn-outline text-sm"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-600 dark:text-gray-400 px-4">
                Page {page} of {totalPages} ({total} total)
              </span>
              <button
                onClick={() => fetchHistory(page + 1)}
                disabled={page >= totalPages}
                className="btn-outline text-sm"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}