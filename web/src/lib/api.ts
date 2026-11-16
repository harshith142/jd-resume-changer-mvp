import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { getSession, signOut } from 'next-auth/react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BACKEND_JWT_KEY = 'backend-jwt-token';
const BACKEND_REFRESH_KEY = 'backend-refresh-token';

const getStoredBackendJwt = () => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(BACKEND_JWT_KEY) || null;
};

const getStoredBackendRefreshJwt = () => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(BACKEND_REFRESH_KEY) || null;
};

const clearStoredBackendAuth = () => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(BACKEND_JWT_KEY);
  localStorage.removeItem(BACKEND_REFRESH_KEY);
};

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const session = await getSession();
    const backendJwt = getStoredBackendJwt();

    if (backendJwt) {
      config.headers.Authorization = `Bearer ${backendJwt}`;
    } else if (session?.accessToken) {
      config.headers.Authorization = `Bearer ${session.accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getStoredBackendRefreshJwt();
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const nextAccessToken = response.data.access_token;
          const nextRefreshToken = response.data.refresh_token;

          if (nextAccessToken) {
            localStorage.setItem(BACKEND_JWT_KEY, nextAccessToken);
          }
          if (nextRefreshToken) {
            localStorage.setItem(BACKEND_REFRESH_KEY, nextRefreshToken);
          }

          originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        clearStoredBackendAuth();
        await signOut({ callbackUrl: '/login' });
        return Promise.reject(refreshError);
      }
    }

    if (error.response?.status === 401) {
      clearStoredBackendAuth();
      await signOut({ callbackUrl: '/login' });
    }

    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  provider: string;
  provider_id: string;
  created_at: string;
  updated_at: string;
}

export type LLMProvider = 'gemini' | 'openai' | 'anthropic' | 'grok' | 'openrouter' | 'nvidia' | 'ollama';

export interface APIKey {
  id: string;
  provider: LLMProvider;
  model?: string | null;
  ollama_host?: string | null;
  is_session_only: boolean;
  has_key: boolean;
  key_preview: string | null;
  is_valid: boolean | null;
  last_tested_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface APIKeyCreate {
  provider: LLMProvider;
  api_key: string;
  model?: string;
  ollama_host?: string;
  is_session_only?: boolean;
}

export interface MasterResume {
  id: string;
  title: string;
  latex_source: string;
  parsed_profile: ResumeProfile | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ResumeProfile {
  name: string;
  email: string;
  phone: string | null;
  location: string | null;
  linkedin: string | null;
  github: string | null;
  portfolio: string | null;
  summary: string;
  skills?: SkillCategory[] | null;
  experience?: Experience[] | null;
  education?: Education[] | null;
  projects?: Project[] | null;
  certifications?: Certification[] | null;
  awards?: Award[] | null;
  publications?: Publication[] | null;
  languages?: Language[] | null;
}

export interface SkillCategory {
  category: string;
  items: string[];
}

export interface Experience {
  title: string;
  company: string;
  location: string | null;
  start_date: string;
  end_date: string | null;
  description: string[];
  technologies: string[];
}

export interface Education {
  degree: string;
  institution: string;
  location: string | null;
  graduation_date: string | null;
  gpa: string | null;
  details: string[];
}

export interface Project {
  name: string;
  description: string;
  technologies: string[];
  url: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string | null;
  url: string | null;
}

export interface Award {
  name: string;
  issuer: string;
  date: string | null;
  description: string | null;
}

export interface Publication {
  title: string;
  venue: string;
  date: string;
  url: string | null;
}

export interface Language {
  language: string;
  proficiency: string;
}

export interface MasterResumeCreate {
  title: string;
  latex_source: string;
  is_default?: boolean;
}

export interface MasterResumeUpdate {
  title?: string;
  latex_source?: string;
  is_default?: boolean;
}

export type JobDescriptionSource = 'paste' | 'upload' | 'url' | 'manual' | 'file';

export interface JobDescription {
  id: string;
  title: string;
  company: string | null;
  location: string | null;
  raw_text: string;
  parsed_profile: JDProfile | null;
  source: JobDescriptionSource;
  source_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface JDProfile {
  title: string;
  company: string | null;
  location: string | null;
  employment_type: string | null;
  seniority_level: string | null;
  required_skills?: SkillRequirement[] | null;
  preferred_skills?: SkillRequirement[] | null;
  responsibilities?: string[] | null;
  qualifications?: string[] | null;
  benefits?: string[] | null;
  salary_range: string | null;
  keywords?: string[] | null;
  culture_signals?: string[] | null;
}

export interface SkillRequirement {
  skill: string;
  importance: 'critical' | 'important' | 'nice-to-have';
  evidence: string | null;
}

export interface JobDescriptionCreate {
  title: string;
  company?: string;
  location?: string;
  raw_text: string;
  source?: JobDescriptionSource;
  source_url?: string;
}

export interface JobDescriptionUpdate {
  title?: string;
  company?: string;
  location?: string;
  raw_text?: string;
  source?: JobDescriptionSource;
  source_url?: string;
}

export interface GeneratedResume {
  id: string;
  master_resume_id: string;
  job_description_id: string;
  master_resume_name?: string | null;
  master_resume_title?: string | null;
  job_description_title?: string | null;
  jd_title?: string | null;
  tailored_latex: string;
  pdf_bytes: string | null; // base64
  ats_score: number | null;
  keyword_match: KeywordMatch | null;
  missing_keywords: string[];
  changes: string[];
  ats_notes: string[];
  page_count: number | null;
  compile_log: string | null;
  llm_provider_used: string;
  llm_model_used: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  generation_time_ms?: number | null;
  created_at: string;
  updated_at?: string;
}

export interface GeneratedResumeListItem {
  id: string;
  master_resume_name?: string | null;
  job_description_title?: string | null;
  tailored_latex?: string | null;
  ats_score: number | null;
  page_count: number | null;
  llm_provider_used: string;
  llm_model_used: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  generation_time_ms?: number | null;
  keyword_match: KeywordMatch | null;
  missing_keywords: string[];
  created_at: string;
  updated_at?: string;
}

export interface KeywordMatch {
  matched_keywords?: string[] | null;
  missing_keywords?: string[] | null;
  match_percentage: number;
}

export interface GenerateResumeRequest {
  master_resume_id: string;
  job_description_id: string;
  target_role?: string;
  llm_provider?: LLMProvider;
  llm_model?: string;
  llm_api_key?: string;
  llm_ollama_host?: string;
  session_api_keys?: Record<string, string>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// API functions
export const authApi = {
  me: () => api.get<User>('/api/v1/auth/me'),
  refresh: (refreshToken: string) => api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/api/v1/auth/logout'),
};

export const userApi = {
  getProfile: () => api.get<User>('/api/v1/users/me'),
  updateProfile: (data: Partial<User>) => api.patch<User>('/api/v1/users/me', data),
};

export const apiKeyApi = {
  list: () => api.get<PaginatedResponse<APIKey>>('/api/v1/api-keys'),
  get: (id: string) => api.get<APIKey>(`/api/v1/api-keys/${id}`),
  create: (data: APIKeyCreate) => api.post<APIKey>('/api/v1/api-keys', data),
  update: (provider: string, data: Partial<APIKeyCreate>) => api.patch<APIKey>(`/api/v1/api-keys/${provider}`, data),
  delete: (provider: string) => api.delete(`/api/v1/api-keys/${provider}`),
  test: (id: string) => api.post<{ is_valid: boolean; error?: string }>(`/api/v1/api-keys/${id}/test`),
};

export const masterResumeApi = {
  list: (params?: { page?: number; size?: number }) =>
    api.get<PaginatedResponse<MasterResume>>('/api/v1/resumes', { params }),
  get: (id: string) => api.get<MasterResume>(`/api/v1/resumes/${id}`),
  create: (data: MasterResumeCreate) => api.post<MasterResume>('/api/v1/resumes', data),
  update: (id: string, data: MasterResumeUpdate) => api.patch<MasterResume>(`/api/v1/resumes/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/resumes/${id}`),
  upload: (file: File, title?: string, isDefault?: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    if (isDefault) formData.append('is_default', 'true');
    return api.post<MasterResume>('/api/v1/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  setDefault: (id: string) => api.post(`/api/v1/resumes/${id}/set-default`),
};

export const jobDescriptionApi = {
  list: (params?: { page?: number; size?: number }) =>
    api.get<PaginatedResponse<JobDescription>>('/api/v1/job-descriptions', { params }),
  get: (id: string) => api.get<JobDescription>(`/api/v1/job-descriptions/${id}`),
  create: (data: JobDescriptionCreate) => api.post<JobDescription>('/api/v1/job-descriptions', data),
  update: (id: string, data: JobDescriptionUpdate) => api.patch<JobDescription>(`/api/v1/job-descriptions/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/job-descriptions/${id}`),
  upload: (file: File, title?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);
    return api.post<JobDescription>('/api/v1/job-descriptions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export interface GenerateResumeResponse {
  generated_resume: GeneratedResume;
  pdf_base64?: string;
}

export const generatedResumeApi = {
  list: (params?: { page?: number; size?: number; master_resume_id?: string; job_description_id?: string }) =>
    api.get<PaginatedResponse<GeneratedResumeListItem>>('/api/v1/generated-resumes', { params }),
  get: (id: string) => api.get<GeneratedResume>(`/api/v1/generated-resumes/${id}`),
  create: (data: GenerateResumeRequest) => api.post<GenerateResumeResponse>(`/api/v1/generated-resumes/generate`, data),
  delete: (id: string) => api.delete(`/api/v1/generated-resumes/${id}`),
  downloadPdf: (id: string) => api.get(`/api/v1/generated-resumes/${id}/download/pdf`, { responseType: 'blob' }),
  downloadTex: (id: string) => api.get(`/api/v1/generated-resumes/${id}/download/tex`, { responseType: 'blob' }),
};