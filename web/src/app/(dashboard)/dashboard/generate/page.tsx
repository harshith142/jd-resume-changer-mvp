'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Loader2,
  FileText,
  Briefcase,
  ArrowRight,
  CheckCircle,
  XCircle,
  AlertCircle,
  Zap,
  Brain,
  Download,
  Eye,
  RefreshCw,
} from 'lucide-react';
import { masterResumeApi, MasterResume } from '@/lib/api';
import { jobDescriptionApi, JobDescription } from '@/lib/api';
import { generatedResumeApi, GenerateResumeRequest, GeneratedResume } from '@/lib/api';
import { toast } from 'sonner';

const generateSchema = z.object({
  master_resume_id: z.string().min(1, 'Select a master resume'),
  job_description_id: z.string().min(1, 'Select a job description'),
  target_role: z.string().optional(),
  llm_provider: z.enum(['gemini', 'openrouter', 'nvidia', 'ollama']).optional(),
  llm_model: z.string().optional(),
});

type GenerateFormData = z.infer<typeof generateSchema>;

const GENERATION_STEPS = [
  { id: 'parse_jd', label: 'Parse Job Description', icon: Brain },
  { id: 'parse_resume', label: 'Parse Master Resume', icon: FileText },
  { id: 'match', label: 'Match Skills & Experience', icon: Zap },
  { id: 'generate', label: 'Generate Tailored LaTeX', icon: Brain },
  { id: 'sanitize', label: 'Sanitize & Validate LaTeX', icon: CheckCircle },
  { id: 'compile', label: 'Compile PDF', icon: FileText },
  { id: 'ats', label: 'Calculate ATS Score', icon: Zap },
];

export default function GeneratePage() {
  const router = useRouter();
  const [masterResumes, setMasterResumes] = useState<MasterResume[]>([]);
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [stepStatus, setStepStatus] = useState<Record<string, 'pending' | 'active' | 'completed' | 'failed'>>({});
  const [generatedResume, setGeneratedResume] = useState<GeneratedResume | null>(null);
  const [polling, setPolling] = useState(false);

  const safeMasterResumes = Array.isArray(masterResumes) ? masterResumes : [];
  const safeJobDescriptions = Array.isArray(jobDescriptions) ? jobDescriptions : [];

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<GenerateFormData>({
    resolver: zodResolver(generateSchema),
    defaultValues: {
      master_resume_id: '',
      job_description_id: '',
      target_role: '',
      llm_provider: undefined,
      llm_model: undefined,
    },
  });

  const selectedResumeId = watch('master_resume_id');
  const selectedJDId = watch('job_description_id');

  const selectedResume = safeMasterResumes.find(r => r.id === selectedResumeId);
  const selectedJD = safeJobDescriptions.find(j => j.id === selectedJDId);
  const generatedMatchedKeywords = generatedResume?.keyword_match?.matched_keywords ?? [];
  const generatedMissingKeywords = generatedResume?.keyword_match?.missing_keywords ?? [];

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        setLoadingOptions(true);
        const [resumesRes, jdsRes] = await Promise.all([
          masterResumeApi.list({ size: 50 }),
          jobDescriptionApi.list({ size: 50 }),
        ]);
        const resumeItems = Array.isArray(resumesRes?.data?.items) ? resumesRes.data.items : [];
        const jdItems = Array.isArray(jdsRes?.data?.items) ? jdsRes.data.items : [];
        setMasterResumes(resumeItems);
        setJobDescriptions(jdItems);

        // Auto-select default resume
        const defaultResume = resumeItems.find(r => r.is_default);
        if (defaultResume && !selectedResumeId) {
          setValue('master_resume_id', defaultResume.id);
        }

        // Auto-select first JD if none selected
        if (jdItems.length > 0 && !selectedJDId) {
          setValue('job_description_id', jdItems[0].id);
        }
      } catch (error) {
        toast.error('Failed to load options');
      } finally {
        setLoadingOptions(false);
      }
    };
    fetchOptions();
  }, [setValue, selectedResumeId, selectedJDId]);

  const initializeSteps = () => {
    const status: Record<string, 'pending' | 'active' | 'completed' | 'failed'> = {};
    GENERATION_STEPS.forEach((step, i) => {
      status[step.id] = i === 0 ? 'active' : 'pending';
    });
    setStepStatus(status);
    setCurrentStep(0);
  };

  const pollGeneration = async (id: string) => {
    setPolling(true);
    try {
      while (true) {
        const response = await generatedResumeApi.get(id);
        const resume = response.data;

        // Update step status based on generation status
        if (resume.status === 'processing') {
          // Could parse progress from error_message or add progress field
        } else if (resume.status === 'completed') {
          GENERATION_STEPS.forEach(step => {
            setStepStatus(prev => ({ ...prev, [step.id]: 'completed' }));
          });
          setGeneratedResume(resume);
          toast.success('Resume generated successfully!');
          break;
        } else if (resume.status === 'failed') {
          GENERATION_STEPS.forEach((step, i) => {
            setStepStatus(prev => ({
              ...prev,
              [step.id]: i <= currentStep ? 'completed' : 'failed',
            }));
          });
          toast.error(resume.error_message || 'Generation failed');
          break;
        }

        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (error) {
      toast.error('Failed to poll generation status');
    } finally {
      setPolling(false);
      setGenerating(false);
    }
  };

  const onSubmit = async (data: GenerateFormData) => {
    if (!selectedResume || !selectedJD) {
      toast.error('Please select both a resume and job description');
      return;
    }

    setGenerating(true);
    setGeneratedResume(null);
    initializeSteps();

    try {
      const payload: GenerateResumeRequest = {
        master_resume_id: data.master_resume_id,
        job_description_id: data.job_description_id,
        target_role: data.target_role || undefined,
        llm_provider: data.llm_provider,
        llm_model: data.llm_model || undefined,
      };

      const response = await generatedResumeApi.create(payload);
      const newGeneration = response.data.generated_resume;
      setGenerationId(newGeneration.id);
      toast.success('Generation started');
      pollGeneration(newGeneration.id);
    } catch (error) {
      toast.error('Failed to start generation');
      setGenerating(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!generationId || !generatedResume) return;
    try {
      const response = await generatedResumeApi.downloadPdf(generationId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const title = generatedResume.jd_title ?? generatedResume.job_description_title ?? 'untitled';
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
    if (!generationId || !generatedResume) return;
    try {
      const response = await generatedResumeApi.downloadTex(generationId);
      const blob = new Blob([response.data], { type: 'text/x-tex' });
      const url = URL.createObjectURL(blob);
      const title = generatedResume.jd_title ?? generatedResume.job_description_title ?? 'untitled';
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}_tailored_resume.tex`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Failed to download LaTeX');
    }
  };

  const handleGenerateAnother = () => {
    setGenerationId(null);
    setGeneratedResume(null);
    initializeSteps();
  };

  if (loadingOptions) {
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Generate Tailored Resume</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Match your resume to a job description with AI</p>
      </div>

      {/* Selection Form */}
      {!generationId && (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="card p-6 space-y-6">
            <h3 className="font-semibold text-gray-900 dark:text-white">Select Inputs</h3>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Master Resume */}
              <div>
                <label className="label">Master Resume *</label>
                <select
                  {...register('master_resume_id')}
                  className={`input ${errors.master_resume_id ? 'border-red-300 dark:border-red-700' : ''}`}
                >
                  <option value="">Choose a resume...</option>
                  {masterResumes.map(resume => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title} {resume.is_default && '(Default)'}
                    </option>
                  ))}
                </select>
                {errors.master_resume_id && (
                  <p className="mt-1 text-sm text-red-500">{errors.master_resume_id.message}</p>
                )}
                {masterResumes.length === 0 && (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    No resumes found. <Link href="/dashboard/resumes/new" className="text-primary-600 hover:underline">Create one</Link>
                  </p>
                )}

                {selectedResume && (
                  <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-sm">
                    <p className="font-medium text-gray-900 dark:text-white">{selectedResume.title}</p>
                    <p className="text-gray-500 dark:text-gray-400">
                      {selectedResume.parsed_profile?.skills?.reduce((a, c) => a + c.items.length, 0) || 0} skills •
                      {selectedResume.parsed_profile?.experience?.length || 0} experiences •
                      {selectedResume.parsed_profile?.education?.length || 0} education
                    </p>
                  </div>
                )}
              </div>

              {/* Job Description */}
              <div>
                <label className="label">Job Description *</label>
                <select
                  {...register('job_description_id')}
                  className={`input ${errors.job_description_id ? 'border-red-300 dark:border-red-700' : ''}`}
                >
                  <option value="">Choose a job description...</option>
                  {jobDescriptions.map(jd => (
                    <option key={jd.id} value={jd.id}>
                      {jd.title} {jd.company && `at ${jd.company}`}
                    </option>
                  ))}
                </select>
                {errors.job_description_id && (
                  <p className="mt-1 text-sm text-red-500">{errors.job_description_id.message}</p>
                )}
                {jobDescriptions.length === 0 && (
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    No job descriptions found. <Link href="/dashboard/job-descriptions/new" className="text-primary-600 hover:underline">Add one</Link>
                  </p>
                )}

                {selectedJD && (
                  <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg text-sm">
                    <p className="font-medium text-gray-900 dark:text-white">{selectedJD.title}</p>
                    {selectedJD.company && <p className="text-gray-500 dark:text-gray-400">{selectedJD.company}</p>}
                    <p className="text-gray-500 dark:text-gray-400">
                      {selectedJD.parsed_profile?.required_skills?.length || 0} required skills •
                      {selectedJD.parsed_profile?.preferred_skills?.length || 0} preferred skills
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Optional Settings */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h4 className="font-medium text-gray-900 dark:text-white mb-4">Advanced Options (Optional)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Target Role</label>
                  <input
                    {...register('target_role')}
                    placeholder="e.g., Staff Engineer, Tech Lead"
                    className="input"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Override the JD title for tailoring focus</p>
                </div>
                <div>
                  <label className="label">LLM Provider</label>
                  <select {...register('llm_provider')} className="input">
                    <option value="">Auto (use your API keys)</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="openrouter">OpenRouter</option>
                    <option value="nvidia">NVIDIA NIM</option>
                    <option value="ollama">Ollama (Local)</option>
                  </select>
                </div>
                <div>
                  <label className="label">Model</label>
                  <input
                    {...register('llm_model')}
                    placeholder="e.g., gemini-1.5-pro, llama-3.1-70b"
                    className="input"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Leave empty for provider default</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end gap-4">
            <Link href="/dashboard" className="btn-secondary">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={generating || !selectedResumeId || !selectedJDId}
              className="btn-primary"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Generate Resume
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* Generation Progress */}
      {generationId && !generatedResume && (
        <div className="card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Generating Tailored Resume</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {selectedResume?.title} → {selectedJD?.title}
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              <Loader2 className="h-4 w-4 animate-spin text-primary-600" />
              <span>Processing...</span>
            </div>
          </div>

          <div className="space-y-3">
            {GENERATION_STEPS.map((step, index) => {
              const status = stepStatus[step.id] || 'pending';
              const Icon = step.icon;
              const isActive = status === 'active';
              const isCompleted = status === 'completed';
              const isFailed = status === 'failed';

              return (
                <div
                  key={step.id}
                  className={`flex items-center gap-4 p-3 rounded-lg transition-colors ${
                    isActive ? 'bg-primary-50 dark:bg-primary-900/10' : ''
                  }`}
                >
                  <div className={`flex items-center justify-center h-8 w-8 rounded-full flex-shrink-0 ${
                    isCompleted ? 'bg-green-500 text-white' :
                    isFailed ? 'bg-red-500 text-white' :
                    isActive ? 'bg-primary-500 text-white animate-pulse' :
                    'bg-gray-200 dark:bg-gray-700 text-gray-400'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : isFailed ? (
                      <XCircle className="h-5 w-5" />
                    ) : isActive ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span className={`font-medium ${
                    isCompleted ? 'text-green-700 dark:text-green-300' :
                    isFailed ? 'text-red-700 dark:text-red-300' :
                    isActive ? 'text-primary-700 dark:text-primary-300' :
                    'text-gray-700 dark:text-gray-300'
                  }`}>
                    {step.label}
                  </span>
                  {isActive && (
                    <span className="text-xs text-primary-600 dark:text-primary-400 animate-pulse">In progress...</span>
                  )}
                  {isCompleted && (
                    <span className="text-xs text-green-600 dark:text-green-400">Done</span>
                  )}
                  {isFailed && (
                    <span className="text-xs text-red-600 dark:text-red-400">Failed</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Result */}
      {generatedResume && (
        <div className="space-y-6">
          <div className="card p-6 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-green-800 dark:text-green-200">Resume Generated Successfully!</h3>
                <p className="text-green-700 dark:text-green-300">
                  {generatedResume.master_resume_title ?? generatedResume.master_resume_name ?? 'Master Resume'} tailored for {generatedResume.jd_title ?? generatedResume.job_description_title ?? 'Job Description'}
                </p>
              </div>
              <div className="ml-auto flex items-center gap-4">
                {generatedResume.ats_score !== null && (
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-700 dark:text-green-300">{generatedResume.ats_score}%</div>
                    <div className="text-xs text-green-600 dark:text-green-400">ATS Score</div>
                  </div>
                )}
                {generatedResume.keyword_match && (
                  <div className="text-center border-l border-green-200 dark:border-green-800 pl-4">
                    <div className="text-3xl font-bold text-primary-700 dark:text-primary-300">{generatedResume.keyword_match.match_percentage}%</div>
                    <div className="text-xs text-primary-600 dark:text-primary-400">Keyword Match</div>
                  </div>
                )}
                {generatedResume.generation_time_ms && (
                  <div className="text-center border-l border-green-200 dark:border-green-800 pl-4">
                    <div className="text-3xl font-bold text-gray-700 dark:text-gray-300">{Math.round(generatedResume.generation_time_ms / 1000)}s</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Generation Time</div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Keyword Match Details */}
          {generatedResume.keyword_match && (
            <div className="card p-6">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-4">Keyword Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium text-green-700 dark:text-green-300 mb-2 flex items-center gap-1">
                    <CheckCircle className="h-4 w-4" /> Matched Keywords ({generatedMatchedKeywords.length})
                  </h5>
                  <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                    {generatedMatchedKeywords.slice(0, 20).map((kw, i) => (
                      <span key={i} className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded">
                        {kw}
                      </span>
                    ))}
                    {generatedMatchedKeywords.length > 20 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">+{generatedMatchedKeywords.length - 20} more</span>
                    )}
                  </div>
                </div>
                <div>
                  <h5 className="font-medium text-red-700 dark:text-red-300 mb-2 flex items-center gap-1">
                    <XCircle className="h-4 w-4" /> Missing Keywords ({generatedMissingKeywords.length})
                  </h5>
                  <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                    {generatedMissingKeywords.slice(0, 20).map((kw, i) => (
                      <span key={i} className="px-2 py-1 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded">
                        {kw}
                      </span>
                    ))}
                    {generatedMissingKeywords.length > 20 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">+{generatedMissingKeywords.length - 20} more</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <button onClick={handleDownloadPdf} className="btn-primary">
                  <Download className="h-4 w-4" />
                  Download PDF
                </button>
                <button onClick={handleDownloadTex} className="btn-outline">
                  <FileText className="h-4 w-4" />
                  Download LaTeX
                </button>
                <Link href={`/dashboard/history/${generationId}`} className="btn-outline">
                  <Eye className="h-4 w-4" />
                  View Details
                </Link>
              </div>
              <button onClick={handleGenerateAnother} className="btn-secondary">
                <RefreshCw className="h-4 w-4" />
                Generate Another
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}