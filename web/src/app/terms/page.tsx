import { Metadata } from 'next';
import Link from 'next/link';
import { FileText, ArrowLeft } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Terms of Service - JD Resume Changer',
  description: 'Terms of Service for JD Resume Changer',
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-primary-600 hover:underline mb-8">
          <ArrowLeft className="h-5 w-5" />
          Back to Home
        </Link>

        <div className="card p-8 sm:p-12">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">Terms of Service</h1>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">1. Acceptance of Terms</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                By accessing and using JD Resume Changer, you accept and agree to be bound by the terms and provision of this agreement.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">2. Description of Service</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                JD Resume Changer is a tool that helps you tailor your resume to job descriptions using AI. The service provides:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>Resume parsing and analysis</li>
                <li>Job description analysis</li>
                <li>AI-powered resume tailoring</li>
                <li>ATS scoring and optimization</li>
                <li>PDF and LaTeX output generation</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">3. User Responsibilities</h2>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>You are responsible for providing accurate information</li>
                <li>You must not use the service for any illegal or unauthorized purpose</li>
                <li>You are responsible for reviewing generated content before use</li>
                <li>You must comply with all applicable laws</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">4. AI-Generated Content</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                The service uses AI to generate tailored resumes. You acknowledge that:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>AI output may contain errors or inaccuracies</li>
                <li>You must review all generated content before submitting to employers</li>
                <li>The service does not guarantee interview outcomes</li>
                <li>You retain ownership of your data and generated content</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">5. API Keys and Third-Party Services</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                You may provide your own API keys for AI providers (Gemini, OpenRouter, NVIDIA, Ollama). You are responsible for:
              </p>
              <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 mt-2 space-y-1">
                <li>Complying with third-party terms of service</li>
                <li>Any costs incurred from API usage</li>
                <li>Securing your API keys</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">6. Data Privacy</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Your data is stored locally or in your configured database. We do not sell or share your data.
                See our <Link href="/privacy" className="text-primary-600 hover:underline">Privacy Policy</Link> for details.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">7. Disclaimer of Warranties</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                The service is provided "as is" without warranties of any kind. We do not warrant that the service will be
                uninterrupted, error-free, or that results will meet your expectations.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">8. Limitation of Liability</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                In no event shall JD Resume Changer be liable for any indirect, incidental, special, consequential, or punitive damages.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">9. Changes to Terms</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                We may modify these terms at any time. Continued use of the service after changes constitutes acceptance.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">10. Contact</h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                For questions about these terms, please contact us through the GitHub repository.
              </p>
            </section>
          </div>

          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Last updated: {new Date().toLocaleDateString()}</p>
            <p className="mt-2">
              <Link href="/privacy" className="text-primary-600 hover:underline">Privacy Policy</Link> •
              <Link href="/" className="text-primary-600 hover:underline ml-2">Home</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}