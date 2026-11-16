'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Briefcase, Upload, FileText, ArrowLeft } from 'lucide-react';
import { jobDescriptionApi, JobDescriptionCreate } from '@/lib/api';
import { toast } from 'sonner';

const jdSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  company: z.string().max(100).optional(),
  location: z.string().max(100).optional(),
  raw_text: z.string().min(50, 'Job description text is required (at least 50 characters)'),
  source: z.enum(['paste', 'upload', 'url', 'manual', 'file']).optional(),
  source_url: z.string().url().optional().or(z.literal('')),
});

type JDFormData = z.infer<typeof jdSchema>;

export default function NewJobDescriptionPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [inputMethod, setInputMethod] = useState<'paste' | 'upload' | 'url'>('paste');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors },
  } = useForm<JDFormData>({
    resolver: zodResolver(jdSchema),
    defaultValues: {
      title: '',
      company: '',
      location: '',
      raw_text: '',
      source: 'manual',
      source_url: '',
    },
  });

  const rawText = watch('raw_text');

  const onSubmit = async (data: JDFormData) => {
    setIsLoading(true);
    try {
      const payload: JobDescriptionCreate = {
        title: data.title,
        company: data.company || undefined,
        location: data.location || undefined,
        raw_text: data.raw_text,
        source: data.source,
        source_url: data.source_url || undefined,
      };
      const response = await jobDescriptionApi.create(payload);
      toast.success('Job description created successfully');
      router.push(`/dashboard/job-descriptions/${response.data.id}`);
    } catch (error) {
      toast.error('Failed to create job description');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload a PDF, DOCX, or TXT file');
      return;
    }

    setIsLoading(true);
    try {
      const response = await jobDescriptionApi.upload(file, watch('title') || undefined);
      const jd = response.data;
      reset({
        title: jd.title,
        company: jd.company || '',
        location: jd.location || '',
        raw_text: jd.raw_text,
        source: 'upload',
        source_url: '',
      });
      toast.success('File uploaded and parsed');
    } catch (error) {
      toast.error('Failed to upload file');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const text = e.clipboardData.getData('text');
    if (text.length > 50) {
      setValue('raw_text', text);
      toast.success('Text pasted');
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/dashboard/job-descriptions" className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2 inline-flex items-center gap-1">
            <ArrowLeft className="h-4 w-4" />
            Job Descriptions
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">New Job Description</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Add a job description for AI-powered resume tailoring</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Input Method Tabs */}
        <div className="card p-2">
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg">
            {(['paste', 'upload', 'url'] as const).map((method) => (
              <button
                key={method}
                type="button"
                onClick={() => {
                  setInputMethod(method);
                  const nextSource = method === 'paste' ? 'paste' : method === 'upload' ? 'upload' : 'url';
                  setValue('source', nextSource);
                }}
                className={`flex-1 py-2 px-4 text-sm font-medium rounded-lg transition-colors ${
                  inputMethod === method
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                {method.charAt(0).toUpperCase() + method.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Title & Meta */}
        <div className="card p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="label">Job Title *</label>
              <input
                {...register('title')}
                placeholder="e.g., Senior Software Engineer"
                className={`input ${errors.title ? 'border-red-300 dark:border-red-700' : ''}`}
              />
              {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title.message}</p>}
            </div>
            <div>
              <label className="label">Company</label>
              <input
                {...register('company')}
                placeholder="Company name (optional)"
                className="input"
              />
            </div>
            <div>
              <label className="label">Location</label>
              <input
                {...register('location')}
                placeholder="City, State / Remote (optional)"
                className="input"
              />
            </div>
          </div>
        </div>

        {/* Content Input */}
        <div className="card p-6 space-y-4">
          {inputMethod === 'paste' && (
            <>
              <label className="label">Job Description Text *</label>
              <textarea
                {...register('raw_text')}
                rows={20}
                className={`w-full p-4 font-mono text-sm border rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y ${
                  errors.raw_text ? 'border-red-300 dark:border-red-700' : ''
                }`}
                placeholder="Paste the full job description here..."
                onPaste={handlePaste}
              />
              {errors.raw_text && <p className="text-sm text-red-500">{errors.raw_text.message}</p>}
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {rawText.length} characters • Minimum 50 characters required
              </p>
            </>
          )}

          {inputMethod === 'upload' && (
            <>
              <label className="label">Upload Job Description File</label>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' : 'border-gray-200 dark:border-gray-700'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="jd-file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                  className="hidden"
                />
                <label htmlFor="jd-file" className="cursor-pointer">
                  <Upload className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500 mb-3" />
                  <p className="text-gray-600 dark:text-gray-400 mb-1">
                    Drag & drop a PDF, DOCX, or TXT file, or click to browse
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Text will be extracted automatically
                  </p>
                </label>
              </div>
              {rawText && (
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">Extracted Text Preview:</p>
                  <textarea
                    value={rawText}
                    readOnly
                    rows={10}
                    className="w-full p-3 font-mono text-sm bg-white dark:bg-gray-900 border rounded text-gray-600 dark:text-gray-400"
                  />
                </div>
              )}
            </>
          )}

          {inputMethod === 'url' && (
            <>
              <label className="label">Job Posting URL</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  {...register('source_url')}
                  placeholder="https://example.com/job-posting"
                  className="input flex-1"
                />
                <button
                  type="button"
                  disabled={isLoading}
                  className="btn-outline whitespace-nowrap"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Fetch'}
                </button>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                We'll attempt to extract the job description from the URL
              </p>
              {rawText && (
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">Extracted Text Preview:</p>
                  <textarea
                    value={rawText}
                    readOnly
                    rows={10}
                    className="w-full p-3 font-mono text-sm bg-white dark:bg-gray-900 border rounded text-gray-600 dark:text-gray-400"
                  />
                </div>
              )}
            </>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <Link href="/dashboard/job-descriptions" className="btn-secondary">
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Job Description'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}