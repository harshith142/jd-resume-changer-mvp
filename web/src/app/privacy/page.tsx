import { Metadata } from 'next';
import Link from 'next/link';
import { FileText, ArrowLeft, Shield, Database, Key, Eye, Lock } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Privacy Policy - JD Resume Changer',
  description: 'Privacy Policy for JD Resume Changer',
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-primary-600 hover:underline mb-8">
          <ArrowLeft className="h-5 w-5" />
          Back to Home
        </Link>

        <div className="card p-8 sm:p-12">
          <div className="flex items-center gap-3 mb-8">
            <div className="h-12 w-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <Shield className="h-6 w-6 text-primary-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Privacy Policy</h1>
          </div>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">1. Data We Collect</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                JD Resume Changer collects the following data to provide the service:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li><strong>Account information:</strong> Name, email, password hash (stored securely), and optional profile details</li>
                <li><strong>Resume data:</strong> LaTeX source, parsed profile (skills, experience, education, projects)</li>
                <li><strong>Job descriptions:</strong> Raw text and parsed analysis</li>
                <li><strong>Generated resumes:</strong> Tailored LaTeX, PDF output, ATS scores</li>
                <li><strong>API keys:</strong> Encrypted storage of your LLM provider keys (optional)</li>
                <li><strong>Usage data:</strong> Timestamps, generation counts, error logs</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">2. How We Use Your Data</h2>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>To authenticate you with your secure email/password account</li>
                <li>To parse and analyze your resume and job descriptions</li>
                <li>To generate tailored resumes using AI providers</li>
                <li>To compile LaTeX to PDF and calculate ATS scores</li>
                <li>To store your history and preferences</li>
                <li>To improve the service (anonymized, aggregated)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">3. Data Storage & Security</h2>
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="flex items-start gap-3 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <Database className="h-6 w-6 text-primary-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">Local Database</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Your data is stored in a local SQLite/PostgreSQL database you control. We do not have access to it.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <Lock className="h-6 w-6 text-primary-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">Encryption</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      API keys are encrypted at rest using AES-GCM. Passwords and refresh tokens are hashed using secure one-way algorithms.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <Key className="h-6 w-6 text-primary-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">Your Keys, Your Control</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      You provide your own LLM API keys. We never see or store them in plain text.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  <Eye className="h-6 w-6 text-primary-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">Transparency</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      All code is open source. You can self-host and verify exactly what happens with your data.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">4. Third-Party Services</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                When you use AI features, your resume and job description text is sent to the LLM provider you configure:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li><strong>Google Gemini:</strong> Governed by Google's Privacy Policy</li>
                <li><strong>OpenRouter:</strong> Governed by OpenRouter's Privacy Policy</li>
                <li><strong>NVIDIA NIM:</strong> Governed by NVIDIA's Privacy Policy</li>
                <li><strong>Ollama (local):</strong> Runs on your machine, no external data transfer</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                We do not share your data with any other third parties.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">5. Local Email Authentication</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Authentication is handled through your email address and password. We store a one-way hash of your password and do not keep plain-text credentials.
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>Email address</li>
                <li>Name</li>
                <li>Hashed credential metadata needed to validate sign-ins</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                We do not retain your password in plain text.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">6. Your Rights</h2>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>Access all data we store about you</li>
                <li>Export your data (resumes, JDs, generated output)</li>
                <li>Delete your account and all associated data</li>
                <li>Revoke API keys at any time</li>
                <li>Opt out of analytics (no analytics by default)</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">7. Data Retention</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Data is retained until you delete it. You can delete individual resumes, job descriptions, or generated
                resumes at any time. Deleting your account removes all data within 30 days.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">8. Cookies & Tracking</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                We use only essential cookies for session management. No tracking cookies, analytics cookies, or
                third-party advertising cookies are used.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">9. Children's Privacy</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                The service is not intended for users under 13. We do not knowingly collect data from children.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">10. Changes to This Policy</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                We may update this policy. Material changes will be announced in the app. Continued use constitutes acceptance.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">11. Contact</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                For privacy questions or to exercise your rights, open an issue on the GitHub repository
                or contact the project maintainers.
              </p>
            </section>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Last updated: {new Date().toLocaleDateString()}</p>
            <p className="mt-2">
              <Link href="/terms" className="text-primary-600 hover:underline">Terms of Service</Link> •
              <Link href="/" className="text-primary-600 hover:underline ml-2">Home</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}