'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Edit, Trash2, Briefcase, Eye, Loader2, Search, Filter } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { jobDescriptionApi, JobDescription, PaginatedResponse } from '@/lib/api';
import { toast } from 'sonner';

export default function JobDescriptionsPage() {
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchJDs = async (pageNum = 1) => {
    try {
      setLoading(true);
      const response = await jobDescriptionApi.list({ page: pageNum, size: 20 });
      const data: PaginatedResponse<JobDescription> = response.data;
      setJds(data.items || []);
      setTotalPages(data.pages);
      setTotal(data.total);
      setPage(data.page);
    } catch (error) {
      toast.error('Failed to load job descriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this job description? This action cannot be undone.')) return;

    setDeletingId(id);
    try {
      await jobDescriptionApi.delete(id);
      toast.success('Job description deleted');
      fetchJDs(page);
    } catch (error) {
      toast.error('Failed to delete job description');
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    fetchJDs(1);
  }, [search]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJDs(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Job Descriptions</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Manage job descriptions for resume tailoring</p>
        </div>
        <Link href="/dashboard/job-descriptions/new" className="btn-primary">
          <Plus className="h-4 w-4" />
          New Job Description
        </Link>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="card p-4">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, company, or keywords..."
              className="input pl-10"
            />
          </div>
          <Filter className="h-5 w-5 text-gray-400 mt-10 self-center" />
        </div>
      </form>

      {/* JDs Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : jds.length === 0 ? (
        <div className="card p-12 text-center">
          <Briefcase className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No job descriptions yet</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">Add a job description to start tailoring resumes</p>
          <Link href="/dashboard/job-descriptions/new" className="btn-primary inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Job Description
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jds.map((jd) => (
              <div key={jd.id} className="card p-6 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1 pr-4">
                    <h3 className="font-semibold text-gray-900 dark:text-white truncate mb-1">{jd.title}</h3>
                    {jd.company && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">{jd.company}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      Updated {formatDistanceToNow(new Date(jd.updated_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>

                {jd.location && (
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-gray-400" /> {jd.location}
                  </p>
                )}

                {jd.parsed_profile && (
                  <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                      <span className="text-green-500">✓</span>
                      <span>Profile parsed successfully</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Required Skills: </span>
                        <span className="font-medium">{jd.parsed_profile.required_skills?.length || 0}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Preferred Skills: </span>
                        <span className="font-medium">{jd.parsed_profile.preferred_skills?.length || 0}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Keywords: </span>
                        <span className="font-medium">{jd.parsed_profile.keywords?.length || 0}</span>
                      </div>
                      <div>
                        <span className="text-gray-500 dark:text-gray-400">Seniority: </span>
                        <span className="font-medium capitalize">{jd.parsed_profile.seniority_level || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Link
                    href={`/dashboard/job-descriptions/${jd.id}`}
                    className="btn-outline flex-1 justify-center text-sm"
                  >
                    <Eye className="h-4 w-4" />
                    View
                  </Link>
                  <Link
                    href={`/dashboard/job-descriptions/${jd.id}/edit`}
                    className="btn-outline flex-1 justify-center text-sm"
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(jd.id)}
                    disabled={deletingId === jd.id}
                    className="btn-outline flex-1 justify-center text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-200 dark:border-red-800"
                  >
                    {deletingId === jd.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => fetchJDs(page - 1)}
                disabled={page <= 1}
                className="btn-outline text-sm"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Page {page} of {totalPages} ({total} total)
              </span>
              <button
                onClick={() => fetchJDs(page + 1)}
                disabled={page >= totalPages}
                className="btn-outline text-sm"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}