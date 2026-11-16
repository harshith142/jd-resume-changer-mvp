'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Edit, Trash2, Copy, Download, Loader2, ArrowLeft, Briefcase, CheckCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { jobDescriptionApi, JobDescription } from '@/lib/api';
import { toast } from 'sonner';

export default function JobDescriptionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [jd, setJd] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchJD = async () => {
      try {
        setLoading(true);
        const response = await jobDescriptionApi.get(id);
        setJd(response.data);
      } catch (error) {
        toast.error('Failed to load job description');
        router.push('/dashboard/job-descriptions');
      } finally {
        setLoading(false);
      }
    };
    fetchJD();
  }, [id, router]);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job description? This action cannot be undone.')) return;

    setDeleting(true);
    try {
      await jobDescriptionApi.delete(id);
      toast.success('Job description deleted');
      router.push('/dashboard/job-descriptions');
    } catch (error) {
      toast.error('Failed to delete job description');
    } finally {
      setDeleting(false);
    }
  };

  const handleCopyText = () => {
    if (jd?.raw_text) {
      navigator.clipboard.writeText(jd.raw_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadText = () => {
    if (jd?.raw_text) {
      const blob = new Blob([jd.raw_text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${jd.title.replace(/\s+/g, '_')}_job_description.txt`;
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

  if (!jd) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <Briefcase className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Job description not found</h3>
          <Link href="/dashboard/job-descriptions" className="text-primary-600 hover:underline">Back to job descriptions</Link>
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
            href="/dashboard/job-descriptions"
            className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Job Descriptions
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{jd.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            {jd.company && <span>{jd.company}</span>}
            {jd.location && <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-gray-400" /> {jd.location}</span>}
            <span>Updated {formatDistanceToNow(new Date(jd.updated_at), { addSuffix: true })}</span>
            {jd.created_at !== jd.updated_at && (
              <> • Created {formatDistanceToNow(new Date(jd.created_at), { addSuffix: true })}</>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Link href={`/dashboard/job-descriptions/${id}/edit`} className="btn-outline">
            <Edit className="h-4 w-4" />
            Edit
          </Link>
          <button
            onClick={handleCopyText}
            className="btn-outline"
            title="Copy text"
          >
            {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
          <button
            onClick={handleDownloadText}
            className="btn-outline"
            title="Download .txt"
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

      {/* Parsed Profile */}
      {jd.parsed_profile && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h3 className="font-semibold text-gray-900 dark:text-white">Parsed Job Profile</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Required Skills */}
            {jd.parsed_profile.required_skills && jd.parsed_profile.required_skills.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-1">
                  <span className="text-red-500">●</span> Required Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {jd.parsed_profile.required_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 text-sm bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-full border border-red-200 dark:border-red-800"
                      title={skill.evidence || ''}
                    >
                      {skill.skill} <span className="text-xs opacity-75">({skill.importance})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Preferred Skills */}
            {jd.parsed_profile.preferred_skills && jd.parsed_profile.preferred_skills.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2 flex items-center gap-1">
                  <span className="text-green-500">●</span> Preferred Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {jd.parsed_profile.preferred_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 text-sm bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 rounded-full border border-green-200 dark:border-green-800"
                      title={skill.evidence || ''}
                    >
                      {skill.skill} <span className="text-xs opacity-75">({skill.importance})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Keywords */}
            {jd.parsed_profile.keywords && jd.parsed_profile.keywords.length > 0 && (
              <div className="md:col-span-2">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Keywords</h4>
                <div className="flex flex-wrap gap-2">
                  {jd.parsed_profile.keywords.map((kw, i) => (
                    <span key={i} className="px-3 py-1 text-sm bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              {jd.parsed_profile.employment_type && (
                <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <p className="text-gray-500 dark:text-gray-400">Employment Type</p>
                  <p className="font-medium capitalize">{jd.parsed_profile.employment_type}</p>
                </div>
              )}
              {jd.parsed_profile.seniority_level && (
                <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <p className="text-gray-500 dark:text-gray-400">Seniority</p>
                  <p className="font-medium capitalize">{jd.parsed_profile.seniority_level}</p>
                </div>
              )}
              {jd.parsed_profile.salary_range && (
                <div className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <p className="text-gray-500 dark:text-gray-400">Salary Range</p>
                  <p className="font-medium">{jd.parsed_profile.salary_range}</p>
                </div>
              )}
            </div>
          </div>

          {/* Responsibilities & Qualifications */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {jd.parsed_profile.responsibilities && jd.parsed_profile.responsibilities.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Responsibilities</h4>
                <ul className="space-y-1">
                  {jd.parsed_profile.responsibilities.map((resp, i) => (
                    <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                      <span className="text-primary-500 mt-1">→</span>
                      <span>{resp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {jd.parsed_profile.qualifications && jd.parsed_profile.qualifications.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Qualifications</h4>
                <ul className="space-y-1">
                  {jd.parsed_profile.qualifications.map((qual, i) => (
                    <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                      <span className="text-primary-500 mt-1">→</span>
                      <span>{qual}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Benefits & Culture Signals */}
          {(jd.parsed_profile.benefits && jd.parsed_profile.benefits.length > 0) ||
          (jd.parsed_profile.culture_signals && jd.parsed_profile.culture_signals.length > 0) ? (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              {jd.parsed_profile.benefits && jd.parsed_profile.benefits.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Benefits</h4>
                  <ul className="space-y-1">
                    {jd.parsed_profile.benefits.map((benefit, i) => (
                      <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                        {benefit}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {jd.parsed_profile.culture_signals && jd.parsed_profile.culture_signals.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white mb-2">Culture Signals</h4>
                  <ul className="space-y-1">
                    {jd.parsed_profile.culture_signals.map((signal, i) => (
                      <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
                        <span className="text-purple-500">◆</span>
                        {signal}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Raw Text */}
      <div className="card">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 dark:text-white">Raw Text</h3>
          <div className="flex items-center gap-2">
            <button onClick={handleCopyText} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button onClick={handleDownloadText} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
              Download .txt
            </button>
          </div>
        </div>
        <div className="p-4">
          <pre className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg overflow-x-auto max-h-[400px] text-sm whitespace-pre-wrap">
            {jd.raw_text}
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
          <Link href="/dashboard/resumes/new" className="btn-outline">
            Add Master Resume
          </Link>
          <Link href="/dashboard/job-descriptions/new" className="btn-outline">
            Add Another Job Description
          </Link>
        </div>
      </div>
    </div>
  );
}