'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import {
  Loader2,
  Key,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Trash2,
  Plus,
  RotateCcw,
  Shield,
  Zap,
  Brain,
  Server,
  Terminal,
  Save,
  AlertTriangle,
} from 'lucide-react';
import { apiKeyApi, APIKey, APIKeyCreate } from '@/lib/api';
import { toast } from 'sonner';

const PROVIDERS = [
  { id: 'gemini', name: 'Google Gemini', icon: Brain, color: 'text-blue-600', bgColor: 'bg-blue-100 dark:bg-blue-900/30', description: 'Google\'s multimodal AI models' },
  { id: 'openai', name: 'OpenAI', icon: Zap, color: 'text-green-600', bgColor: 'bg-green-100 dark:bg-green-900/30', description: 'GPT-4o, GPT-4, and more' },
  { id: 'anthropic', name: 'Anthropic Claude', icon: Shield, color: 'text-purple-600', bgColor: 'bg-purple-100 dark:bg-purple-900/30', description: 'Claude 3.5 Sonnet, Haiku, Opus' },
  { id: 'grok', name: 'Grok (xAI)', icon: Server, color: 'text-orange-600', bgColor: 'bg-orange-100 dark:bg-orange-900/30', description: 'xAI\'s Grok models' },
  { id: 'openrouter', name: 'OpenRouter', icon: Zap, color: 'text-pink-600', bgColor: 'bg-pink-100 dark:bg-pink-900/30', description: 'Access 100+ models via single API' },
  { id: 'nvidia', name: 'NVIDIA NIM', icon: Server, color: 'text-emerald-600', bgColor: 'bg-emerald-100 dark:bg-emerald-900/30', description: 'NVIDIA\'s optimized inference microservices' },
  { id: 'ollama', name: 'Ollama (Local)', icon: Terminal, color: 'text-amber-600', bgColor: 'bg-amber-100 dark:bg-amber-900/30', description: 'Run models locally on your machine' },
] as const;

type ProviderId = typeof PROVIDERS[number]['id'];

export default function SettingsPage() {
  const { data: session } = useSession();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState<ProviderId | null>(null);
  const [createForm, setCreateForm] = useState({ api_key: '', is_session_only: false });
  const [creating, setCreating] = useState(false);
  const [showKeyId, setShowKeyId] = useState<string | null>(null);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const response = await apiKeyApi.list();
      const items = Array.isArray(response.data?.items)
        ? response.data.items
        : Array.isArray(response.data)
          ? response.data
          : [];
      setApiKeys(items);
    } catch (error) {
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const response = await apiKeyApi.test(id);
      if (response.data.is_valid) {
        toast.success('API key is valid!');
        setApiKeys(prev => prev.map(k => k.id === id ? { ...k, is_valid: true, last_tested_at: new Date().toISOString() } : k));
      } else {
        toast.error(response.data.error || 'API key is invalid');
        setApiKeys(prev => prev.map(k => k.id === id ? { ...k, is_valid: false } : k));
      }
    } catch (error) {
      toast.error('Failed to test API key');
    } finally {
      setTestingId(null);
    }
  };

  const handleDelete = async (provider: string) => {
    if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) return;

    setDeletingId(provider);
    try {
      await apiKeyApi.delete(provider);
      toast.success('API key deleted');
      setApiKeys(prev => prev.filter(k => k.provider !== provider));
    } catch (error) {
      toast.error('Failed to delete API key');
    } finally {
      setDeletingId(null);
    }
  };

  const handleCreate = async (provider: ProviderId) => {
    if (!createForm.api_key.trim()) {
      toast.error('Please enter an API key');
      return;
    }

    setCreating(true);
    try {
      const payload: APIKeyCreate = {
        provider,
        api_key: createForm.api_key,
        is_session_only: createForm.is_session_only,
      };
      const response = await apiKeyApi.create(payload);
      toast.success(`${provider} API key added`);
      setApiKeys(prev => [...prev, response.data]);
      setShowCreateModal(null);
      setCreateForm({ api_key: '', is_session_only: false });
    } catch (error) {
      toast.error('Failed to add API key');
    } finally {
      setCreating(false);
    }
  };

  const getProviderInfo = (provider: string) => {
    return PROVIDERS.find(p => p.id === provider) || PROVIDERS[0];
  };

  const getKeyPreview = (key?: string | null) => {
    if (!key || key.length <= 8) return '••••••••';
    return key.slice(0, 4) + '••••' + key.slice(-4);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">Manage your account and API keys</p>
      </div>

      {/* Profile Section */}
      <div className="card p-6">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Profile</h2>
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            {session?.user?.image ? (
              <img src={session.user.image} alt="" className="h-16 w-16 rounded-full" />
            ) : (
              <Shield className="h-8 w-8 text-primary-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">{session?.user?.name}</h3>
            <p className="text-gray-500 dark:text-gray-400">{session?.user?.email}</p>
            <p className="text-sm text-gray-400 mt-1">Provider: {(session as any)?.user?.provider || 'Email'}</p>
          </div>
        </div>
      </div>

      {/* API Keys Section */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-semibold text-gray-900 dark:text-white">API Keys</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">Keys are encrypted with AES-256-GCM</p>
        </div>

        {/* Provider Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {PROVIDERS.map((provider) => {
            const keys = apiKeys.filter(k => k.provider === provider.id);
            const hasValidKey = keys.some(k => k.is_valid);
            const Icon = provider.icon;

            return (
              <div key={provider.id} className={`p-4 rounded-lg border-2 transition-colors ${provider.bgColor} border-transparent hover:border-opacity-50`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-lg ${provider.bgColor} flex items-center justify-center`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{provider.name}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{provider.description}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${hasValidKey ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}>
                    {hasValidKey ? 'Connected' : 'Not Connected'}
                  </span>
                </div>

                {keys.length > 0 ? (
                  <div className="space-y-2">
                    {keys.map((key) => (
                      <div key={key.id} className="flex items-center justify-between p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900 px-2 py-1 rounded">
                            {getKeyPreview(key.key_preview)}
                          </span>
                          <div className="flex items-center gap-2">
                            {key.is_session_only && (
                              <span className="px-2 py-0.5 text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded">Session Only</span>
                            )}
                            <span className={`px-2 py-0.5 text-xs rounded-full ${key.is_valid ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}>
                              {key.is_valid ? 'Valid' : 'Untested'}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleTest(key.id)}
                            disabled={testingId === key.id}
                            className="btn-outline text-sm p-2"
                            title="Test connection"
                          >
                            {testingId === key.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : key.is_valid ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                              <RotateCcw className="h-4 w-4" />
                            )}
                          </button>
                          <button
                            onClick={() => setShowKeyId(showKeyId === key.id ? null : key.id)}
                            className="btn-outline text-sm p-2"
                            title={showKeyId === key.id ? 'Hide' : 'Show'}
                          >
                            {showKeyId === key.id ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                          <button
                            onClick={() => handleDelete(key.provider)}
                            disabled={deletingId === key.provider}
                            className="btn-outline text-sm p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-200 dark:border-red-800"
                            title="Delete"
                          >
                            {deletingId === key.provider ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <button
                    onClick={() => {
                      setCreateForm({ api_key: '', is_session_only: false });
                      setShowCreateModal(provider.id);
                    }}
                    className="w-full btn-outline border-dashed"
                  >
                    <Plus className="h-4 w-4" />
                    Add {provider.name} Key
                  </button>
                )}

                {keys.length > 0 && (
                  <button
                    onClick={() => {
                      setCreateForm({ api_key: '', is_session_only: false });
                      setShowCreateModal(provider.id);
                    }}
                    className="w-full btn-outline text-sm mt-2"
                  >
                    <Plus className="h-4 w-4" />
                    Add Another Key
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Info Box */}
        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
              <p className="font-medium">How API Keys Work</p>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>Encrypted Storage:</strong> Keys are encrypted with AES-256-GCM using a per-user key derived via HKDF-SHA256</li>
                <li><strong>Session-Only Option:</strong> Enable "Session Only" to keep keys in memory only (not stored in database)</li>
                <li><strong>Priority Order:</strong> Request headers (session) → Your encrypted keys → Server defaults (not in production)</li>
                <li><strong>No Server Keys in Production:</strong> You must provide your own API keys for Gemini, OpenRouter, NVIDIA, or use Ollama locally</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Create Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="card w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Add {PROVIDERS.find(p => p.id === showCreateModal)?.name} API Key
              </h3>
              <button
                onClick={() => setShowCreateModal(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">API Key</label>
                <input
                  type="password"
                  value={createForm.api_key}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, api_key: e.target.value }))}
                  placeholder={`Enter your ${showCreateModal} API key`}
                  className="input"
                  autoFocus
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.is_session_only}
                  onChange={(e) => setCreateForm(prev => ({ ...prev, is_session_only: e.target.checked }))}
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Session only (not stored in database)</span>
              </label>

              <p className="text-xs text-gray-500 dark:text-gray-400">
                {showCreateModal === 'gemini' && 'Get your key from <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener" className="text-primary-600 hover:underline">Google AI Studio</a>'}
                {showCreateModal === 'openai' && 'Get your key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" className="text-primary-600 hover:underline">OpenAI Platform</a>'}
                {showCreateModal === 'anthropic' && 'Get your key from <a href="https://console.anthropic.com/" target="_blank" rel="noopener" className="text-primary-600 hover:underline">Anthropic Console</a>'}
                {showCreateModal === 'grok' && 'Get your key from <a href="https://console.x.ai/" target="_blank" rel="noopener" className="text-primary-600 hover:underline">xAI Console</a>'}
                {showCreateModal === 'openrouter' && 'Get your key from <a href="https://openrouter.ai/keys" target="_blank" rel="noopener" className="text-primary-600 hover:underline">OpenRouter</a>'}
                {showCreateModal === 'nvidia' && 'Get your key from <a href="https://build.nvidia.com/explore/discover" target="_blank" rel="noopener" className="text-primary-600 hover:underline">NVIDIA Build</a>'}
                {showCreateModal === 'ollama' && 'Ensure Ollama is running locally at http://localhost:11434. <a href="https://ollama.com" target="_blank" rel="noopener" className="text-primary-600 hover:underline">Download Ollama</a>'}
              </p>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleCreate(showCreateModal)}
                  disabled={creating}
                  className="btn-primary"
                >
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    'Add Key'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Show Key Modal */}
      {showKeyId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="card w-full max-w-md p-6">
            {(() => {
              const key = apiKeys.find(k => k.id === showKeyId);
              return (
                <>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">API Key</h3>
                  <div className="p-4 bg-gray-100 dark:bg-gray-900 rounded-lg font-mono text-sm break-all mb-4">
                    {key ? key.key_preview : 'Loading...'}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">This is a preview. Full key cannot be displayed for security.</p>
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={() => setShowKeyId(null)}
                      className="btn-primary"
                    >
                      Done
                    </button>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}