'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, FileText, Upload, ArrowLeft, Download, Copy, CheckCircle } from 'lucide-react';
import { masterResumeApi, MasterResume, MasterResumeUpdate } from '@/lib/api';
import { toast } from 'sonner';

const resumeSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100),
  latex_source: z.string().min(10, 'LaTeX content is required'),
  is_default: z.boolean().optional(),
});

type ResumeFormData = z.infer<typeof resumeSchema>;

export default function EditResumePage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [isLoading, setIsLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [dragActive, setDragActive] = useState(false);
  const [copied, setCopied] = useState(false);
  const [previewMode, setPreviewMode] = useState<'edit' | 'split' | 'preview'>('edit');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isDirty },
  } = useForm<ResumeFormData>({
    resolver: zodResolver(resumeSchema),
    defaultValues: {
      title: '',
      latex_source: '',
      is_default: false,
    },
  });

  const latexSource = watch('latex_source');

  useEffect(() => {
    const fetchResume = async () => {
      try {
        const response = await masterResumeApi.get(id);
        const resume = response.data;
        reset({
          title: resume.title,
          latex_source: resume.latex_source,
          is_default: resume.is_default,
        });
      } catch (error) {
        toast.error('Failed to load resume');
        router.push('/dashboard/resumes');
      } finally {
        setInitialLoading(false);
      }
    };
    fetchResume();
  }, [id, router, reset]);

  const onSubmit = async (data: ResumeFormData) => {
    if (!isDirty) {
      toast.info('No changes to save');
      return;
    }

    setIsLoading(true);
    try {
      const payload: MasterResumeUpdate = {
        title: data.title,
        latex_source: data.latex_source,
        is_default: data.is_default,
      };
      await masterResumeApi.update(id, payload);
      toast.success('Resume updated successfully');
      router.push(`/dashboard/resumes/${id}`);
    } catch (error) {
      toast.error('Failed to update resume');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.tex') && !file.name.endsWith('.txt')) {
      toast.error('Please upload a .tex or .txt file');
      return;
    }

    const text = await file.text();
    setValue('latex_source', text);
    if (!watch('title')) {
      setValue('title', file.name.replace(/\.[^/.]+$/, ''));
    }
    toast.success('File loaded');
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
    if (text.length > 100) {
      setValue('latex_source', text);
      toast.success('LaTeX pasted');
    }
  };

  const handleCopyLatex = () => {
    if (latexSource) {
      navigator.clipboard.writeText(latexSource);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadTex = () => {
    if (latexSource) {
      const title = watch('title') || 'resume';
      const blob = new Blob([latexSource], { type: 'text/x-tex' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}.tex`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  if (initialLoading) {
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

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/dashboard/resumes/${id}`} className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Edit Resume</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Update your master resume LaTeX source</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Title & Options */}
        <div className="card p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="label">Resume Title *</label>
              <input
                {...register('title')}
                placeholder="e.g., Senior Software Engineer Resume"
                className={`input ${errors.title ? 'border-red-300 dark:border-red-700' : ''}`}
              />
              {errors.title && <p className="mt-1 text-sm text-red-500">{errors.title.message}</p>}
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  {...register('is_default')}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Set as default</span>
              </label>
            </div>
          </div>
        </div>

        {/* Upload Zone */}
        <div
          className={`card border-2 border-dashed transition-colors ${
            dragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' : 'border-gray-200 dark:border-gray-700'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="p-6 text-center">
            <Upload className="h-10 w-10 mx-auto text-gray-400 dark:text-gray-500 mb-3" />
            <p className="text-gray-600 dark:text-gray-400 mb-1">
              Drag & drop a .tex or .txt file, or paste LaTeX below
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              File will populate the editor automatically
            </p>
          </div>
        </div>

        {/* Editor Toolbar */}
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 border-r border-gray-200 dark:border-gray-700 pr-4">
              <FileText className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">LaTeX Editor</span>
            </div>

            <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              {(['edit', 'split', 'preview'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setPreviewMode(mode)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    previewMode === mode
                      ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>

            <div className="flex-1" />

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 font-mono">
              <span>{latexSource.split('\n').length} lines • {latexSource.length} chars</span>
              {isDirty && <span className="text-yellow-500">● Unsaved changes</span>}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopyLatex}
                className="btn-outline text-sm"
              >
                {copied ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              </button>
              <button
                type="button"
                onClick={handleDownloadTex}
                className="btn-outline text-sm"
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Editor / Preview */}
        <div className="card overflow-hidden">
          {previewMode === 'edit' && (
            <div className="p-0">
              <textarea
                {...register('latex_source')}
                className="w-full h-[600px] p-4 font-mono text-sm bg-gray-950 text-gray-100 border-none resize-none focus:outline-none"
                placeholder="Paste your LaTeX resume here..."
                onPaste={handlePaste}
                spellCheck={false}
              />
              {errors.latex_source && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-sm">
                  {errors.latex_source.message}
                </div>
              )}
            </div>
          )}

          {previewMode === 'split' && (
            <div className="grid grid-cols-2 h-[600px]">
              <div className="border-r border-gray-200 dark:border-gray-700">
                <textarea
                  {...register('latex_source')}
                  className="w-full h-full p-4 font-mono text-sm bg-gray-950 text-gray-100 border-none resize-none focus:outline-none"
                  placeholder="Paste your LaTeX resume here..."
                  onPaste={handlePaste}
                  spellCheck={false}
                />
              </div>
              <div className="p-4 overflow-y-auto bg-white dark:bg-gray-900">
                <div className="prose prose-sm dark:prose-invert max-w-none p-4 bg-white dark:bg-gray-900">
                  <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">
                    {latexSource}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {previewMode === 'preview' && (
            <div className="p-6 overflow-y-auto h-[600px] bg-white dark:bg-gray-900">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <pre className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap font-mono">
                  {latexSource}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <Link href={`/dashboard/resumes/${id}`} className="btn-secondary">
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isLoading || !isDirty}
            className="btn-primary"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}