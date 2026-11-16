'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus, Edit, Trash2, Star, FileText, Eye, Download, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { masterResumeApi, MasterResume } from '@/lib/api';
import { toast } from 'sonner';

export default function ResumesPage() {
  const router = useRouter();
  const [resumes, setResumes] = useState<MasterResume[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [settingDefaultId, setSettingDefaultId] = useState<string | null>(null);

  const safeResumes = Array.isArray(resumes) ? resumes : [];

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const response = await masterResumeApi.list({ size: 50 });
      const items = Array.isArray(response?.data?.items) ? response.data.items : [];
      setResumes(items);
    } catch (error) {
      toast.error('Failed to load resumes');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this resume? This action cannot be undone.')) return;

    setDeletingId(id);
    try {
      await masterResumeApi.delete(id);
      toast.success('Resume deleted');
      fetchResumes();
    } catch (error) {
      toast.error('Failed to delete resume');
    } finally {
      setDeletingId(null);
    }
  };

  const handleSetDefault = async (id: string) => {
    setSettingDefaultId(id);
    try {
      await masterResumeApi.setDefault(id);
      toast.success('Default resume updated');
      fetchResumes();
    } catch (error) {
      toast.error('Failed to set default');
    } finally {
      setSettingDefaultId(null);
    }
  };

  // Fetch on mount
  const [fetched, setFetched] = useState(false);
  if (!fetched) {
    setFetched(true);
    fetchResumes();
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Master Resumes</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Manage your base resumes for tailoring</p>
        </div>
        <Link href="/dashboard/resumes/new" className="btn-primary">
          <Plus className="h-4 w-4" />
          New Resume
        </Link>
      </div>

      {/* Resumes Grid */}
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
      ) : safeResumes.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No resumes yet</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">Create your first master resume to start tailoring</p>
          <Link href="/dashboard/resumes/new" className="btn-primary inline-flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create Resume
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {safeResumes.map((resume) => (
            <div key={resume.id} className="card p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 pr-4">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white truncate">{resume.title}</h3>
                    {resume.is_default && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                        <Star className="h-3 w-3 fill-current" />
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Updated {formatDistanceToNow(new Date(resume.updated_at), { addSuffix: true })}
                  </p>
                </div>
              </div>

              {resume.parsed_profile && (
                <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>Profile parsed successfully</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Skills: </span>
                      <span className="font-medium">{resume.parsed_profile.skills?.reduce((acc, cat) => acc + cat.items.length, 0) || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Experience: </span>
                      <span className="font-medium">{resume.parsed_profile.experience?.length || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Education: </span>
                      <span className="font-medium">{resume.parsed_profile.education?.length || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Projects: </span>
                      <span className="font-medium">{resume.parsed_profile.projects?.length || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Link
                  href={`/dashboard/resumes/${resume.id}`}
                  className="btn-outline flex-1 justify-center text-sm"
                >
                  <Eye className="h-4 w-4" />
                  View
                </Link>
                <Link
                  href={`/dashboard/resumes/${resume.id}/edit`}
                  className="btn-outline flex-1 justify-center text-sm"
                >
                  <Edit className="h-4 w-4" />
                  Edit
                </Link>
                {!resume.is_default && (
                  <button
                    onClick={() => handleSetDefault(resume.id)}
                    disabled={settingDefaultId === resume.id}
                    className="btn-outline flex-1 justify-center text-sm"
                    title="Set as default"
                  >
                    {settingDefaultId === resume.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Star className="h-4 w-4" />
                    )}
                  </button>
                )}
                <button
                  onClick={() => handleDelete(resume.id)}
                  disabled={deletingId === resume.id}
                  className="btn-outline flex-1 justify-center text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-200 dark:border-red-800"
                >
                  {deletingId === resume.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}