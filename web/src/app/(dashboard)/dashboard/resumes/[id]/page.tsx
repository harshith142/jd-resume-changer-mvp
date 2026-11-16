'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Edit, Trash2, Star, Copy, Download, Loader2, ArrowLeft, FileText, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { masterResumeApi, MasterResume } from '@/lib/api';
import { toast } from 'sonner';

export default function ResumeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [resume, setResume] = useState<MasterResume | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [settingDefault, setSettingDefault] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchResume = async () => {
      try {
        setLoading(true);
        const response = await masterResumeApi.get(id);
        setResume(response.data);
      } catch (error) {
        toast.error('Failed to load resume');
        router.push('/dashboard/resumes');
      } finally {
        setLoading(false);
      }
    };
    fetchResume();
  }, [id, router]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this resume? This action cannot be undone.')) return;

    setDeleting(true);
    try {
      await masterResumeApi.delete(id);
      toast.success('Resume deleted');
      router.push('/dashboard/resumes');
    } catch (error) {
      toast.error('Failed to delete resume');
    } finally {
      setDeleting(false);
    }
  };

  const handleSetDefault = async () => {
    if (resume?.is_default) return;
    setSettingDefault(true);
    try {
      await masterResumeApi.setDefault(id);
      toast.success('Default resume updated');
      setResume(prev => prev ? { ...prev, is_default: true } : null);
    } catch (error) {
      toast.error('Failed to set default');
    } finally {
      setSettingDefault(false);
    }
  };

  const handleCopyLatex = () => {
    if (resume?.latex_source) {
      navigator.clipboard.writeText(resume.latex_source);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadTex = () => {
    if (resume?.latex_source) {
      const blob = new Blob([resume.latex_source], { type: 'text/x-tex' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${resume.title.replace(/\s+/g, '_')}.tex`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
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

  if (!resume) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <FileText className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Resume not found</h3>
          <Link href="/dashboard/resumes" className="text-primary-600 hover:underline">Back to resumes</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Link
            href="/dashboard/resumes"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Resumes
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{resume.title}</h1>
            {resume.is_default && (
              <span className="flex items-center gap-1 px-3 py-1 text-sm font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full">
                <Star className="h-4 w-4 fill-current" />
                Default
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Updated {formatDistanceToNow(new Date(resume.updated_at), { addSuffix: true })}
            {resume.created_at !== resume.updated_at && (
              <> • Created {formatDistanceToNow(new Date(resume.created_at), { addSuffix: true })}</>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link href={`/dashboard/resumes/${id}/edit`} className="btn-outline">
            <Edit className="h-4 w-4" />
            Edit
          </Link>
          {!resume.is_default && (
            <button
              onClick={handleSetDefault}
              disabled={settingDefault}
              className="btn-outline"
              title="Set as default"
            >
              {settingDefault ? <Loader2 className="h-4 w-4 animate-spin" /> : <Star className="h-4 w-4" />}
            </button>
          )}
          <button
            onClick={handleCopyLatex}
            className="btn-outline"
            title="Copy LaTeX"
          >
            {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
          <button
            onClick={handleDownloadTex}
            className="btn-outline"
            title="Download .tex"
          >
            <Download className="h-4 w-4" />
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

      {/* Parsed Profile Summary */}
      {resume.parsed_profile && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Profile Parsed Successfully</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">Skills</p>
              <p className="font-bold text-gray-900 dark:text-white">
                {resume.parsed_profile.skills?.reduce((acc, cat) => acc + cat.items.length, 0) || 0}
              </p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">Experience</p>
              <p className="font-bold text-gray-900 dark:text-white">{resume.parsed_profile.experience?.length || 0}</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">Education</p>
              <p className="font-bold text-gray-900 dark:text-white">{resume.parsed_profile.education?.length || 0}</p>
            </div>
            <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">Projects</p>
              <p className="font-bold text-gray-900 dark:text-white">{resume.parsed_profile.projects?.length || 0}</p>
            </div>
          </div>

          {resume.parsed_profile.skills && resume.parsed_profile.skills.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Skill Categories</h4>
              <div className="flex flex-wrap gap-2">
                {resume.parsed_profile.skills.map((cat, i) => (
                  <span key={i} className="px-3 py-1 text-sm bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full">
                    {cat.category} ({cat.items.length})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* LaTeX Source */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 dark:text-white">LaTeX Source</h3>
          <div className="flex items-center gap-2">
            <button onClick={handleCopyLatex} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button onClick={handleDownloadTex} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              Download .tex
            </button>
          </div>
        </div>
        <div className="p-4">
          <pre className="bg-gray-950 text-gray-100 p-4 rounded-lg overflow-x-auto max-h-[500px] font-mono text-sm">
            <code>{resume.latex_source}</code>
          </pre>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/dashboard/generate" className="btn-primary">
            Generate Tailored Resume
          </Link>
          <Link href="/dashboard/job-descriptions/new" className="btn-outline">
            Add Job Description
          </Link>
          <Link href="/dashboard/resumes/new" className="btn-outline">
            Create Another Resume
          </Link>
        </div>
      </div>
    </div>
  );
}