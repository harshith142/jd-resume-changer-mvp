'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, FileText, Upload, ChevronDown, X } from 'lucide-react';
import { masterResumeApi, MasterResumeCreate } from '@/lib/api';
import { toast } from 'sonner';

const resumeSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100),
  latex_source: z.string().min(10, 'LaTeX content is required'),
  is_default: z.boolean().optional(),
});

type ResumeFormData = z.infer<typeof resumeSchema>;

const LATEX_TEMPLATE = `\\documentclass[10pt,a4paper]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[margin=0.75in]{geometry}
\\usepackage{enumitem}
\\usepackage{titlesec}
\\usepackage{hyperref}
\\usepackage{xcolor}

\\definecolor{primary}{HTML}{2563EB}
\\hypersetup{colorlinks=true,urlcolor=primary,linkcolor=primary}

\\titleformat{\\section}{\\large\\bfseries\\color{primary}}{}{0em}{}[]\\titlespacing*{\\section}{0pt}{12pt}{6pt}
\\titleformat{\\subsection}{\\normalsize\\bfseries}{}{0em}{}[]\\titlespacing*{\\subsection}{0pt}{8pt}{4pt}

\\setlist[itemize]{leftmargin=*,topsep=2pt,itemsep=2pt}
\\pagenumbering{gobble}

\\begin{document}

% ===== HEADER =====
\\begin{center}
    {\\LARGE \\textbf{Your Name}} \\\\[4pt]
    {\\color{gray} City, State | Phone | Email} \\\\[2pt]
    {\\color{gray} \\href{https://linkedin.com/in/yourprofile}{LinkedIn} | \\href{https://github.com/yourprofile}{GitHub} | \\href{https://yourportfolio.com}{Portfolio}}
\\end{center}

% ===== PROFESSIONAL SUMMARY =====
\\section*{Professional Summary}
Results-driven software engineer with X+ years of experience building scalable systems...
\\vspace{4pt}

% ===== TECHNICAL SKILLS =====
\\section*{Technical Skills}
\\begin{itemize}
    \\item \\textbf{Languages:} Python, TypeScript, Go, Rust, SQL
    \\item \\textbf{Frameworks:} React, Next.js, FastAPI, Django, gRPC
    \\item \\textbf{Cloud/DevOps:} AWS, Docker, Kubernetes, Terraform, CI/CD
    \\item \\textbf{Databases:} PostgreSQL, Redis, MongoDB, DynamoDB
    \\item \\textbf{Tools:} Git, Linux, Monitoring, Testing
\\end{itemize}
\\vspace{4pt}

% ===== EXPERIENCE =====
\\section*{Professional Experience}
\\textbf{Senior Software Engineer} \\hfill Company Name \\hfill 2022--Present \\\\
\\textit{Location (Remote)} \\\\
\\begin{itemize}
    \\item Led architecture redesign reducing latency by 40\\% and costs by 30\\%
    \\item Built event-driven microservices processing 10M+ requests/day
    \\item Mentored 5 engineers; established code review and testing standards
\\end{itemize}
\\vspace{4pt}

\\textbf{Software Engineer} \\hfill Previous Company \\hfill 2020--2022 \\\\
\\textit{Location} \\\\
\\begin{itemize}
    \\item Developed full-stack features for B2B SaaS platform serving 50k+ users
    \\item Implemented real-time collaboration using WebSockets and CRDTs
    \\item Reduced deployment time 80\\% via CI/CD pipeline optimization
\\end{itemize}
\\vspace{4pt}

% ===== EDUCATION =====
\\section*{Education}
\\textbf{M.S. Computer Science} \\hfill University Name \\hfill 2020 \\\\
\\textit{Relevant Coursework:} Distributed Systems, ML, Algorithms \\\\
\\vspace{4pt}

\\textbf{B.S. Computer Engineering} \\hfill University Name \\hfill 2018 \\\\

% ===== PROJECTS =====
\\section*{Key Projects}
\\textbf{Project Name} | \\href{https://github.com/...}{GitHub} \\\\
Tech stack: React, Node.js, PostgreSQL \\\\
Brief description of impact and technologies used. \\\\
\\vspace{4pt}

% ===== CERTIFICATIONS =====
\\section*{Certifications}
\\begin{itemize}
    \\item AWS Solutions Architect Professional (2023)
    \\item Kubernetes Administrator (CKA) (2022)
\\end{itemize}

\\end{document}`;

export default function NewResumePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [previewMode, setPreviewMode] = useState<'edit' | 'split' | 'preview'>('edit');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ResumeFormData>({
    resolver: zodResolver(resumeSchema),
    defaultValues: {
      title: '',
      latex_source: LATEX_TEMPLATE,
      is_default: false,
    },
  });

  const latexSource = watch('latex_source');

  const onSubmit = async (data: ResumeFormData) => {
    setIsLoading(true);
    try {
      const payload: MasterResumeCreate = {
        title: data.title,
        latex_source: data.latex_source,
        is_default: data.is_default,
      };
      const response = await masterResumeApi.create(payload);
      toast.success('Resume created successfully');
      router.push(`/dashboard/resumes/${response.data.id}`);
    } catch (error) {
      toast.error('Failed to create resume');
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

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/dashboard/resumes" className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-2 inline-flex items-center gap-1">
            <FileText className="h-4 w-4" />
            Resumes
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">New Master Resume</h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">Create a base resume in LaTeX format for AI tailoring</p>
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

            <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">
              {latexSource.split('\n').length} lines • {latexSource.length} chars
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
          <Link href="/dashboard/resumes" className="btn-secondary">
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
              'Create Resume'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}