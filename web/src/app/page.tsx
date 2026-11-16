import Link from 'next/link';
import { FileText, Brain, Shield, Download, Github, Linkedin } from 'lucide-react';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-primary-50 to-white dark:from-gray-900 dark:to-gray-950">
      {/* Navigation */}
      <nav className="border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900 dark:text-white">JD Resume Changer</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/login" className="btn-secondary">
                Sign In
              </Link>
              <Link href="/login" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 dark:text-white tracking-tight">
            Tailor Your Resume to{' '}
            <span className="text-primary-600">Any Job Description</span>
            {' '}in Seconds
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Upload your master resume, paste a job description, and let AI generate an ATS-optimized,
            tailored resume that highlights your relevant experience and keywords.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/login" className="btn-primary text-lg px-8 py-3 w-full sm:w-auto">
              Start Free — No Credit Card
            </Link>
            <Link href="#features" className="btn-outline text-lg px-8 py-3 w-full sm:w-auto">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            Everything You Need to Land Interviews
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            Powerful features built for modern job seekers
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: Brain,
              title: 'AI-Powered Tailoring',
              description:
                'Uses Gemini, OpenRouter, NVIDIA, or local Ollama to intelligently match your experience to job requirements while keeping everything truthful.',
            },
            {
              icon: Shield,
              title: 'ATS Optimization',
              description:
                'Built-in ATS scoring with keyword matching, structure analysis, and quantification metrics to maximize your resume\'s parseability.',
            },
            {
              icon: Download,
              title: 'PDF & LaTeX Output',
              description:
                'Get both a professionally compiled PDF and the editable .tex source. Full control over your final resume.',
            },
          ].map((feature, i) => (
            <div key={i} className="card p-6 hover:shadow-lg transition-shadow">
              <div className="h-12 w-12 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-4">
                <feature.icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-gray-50 dark:bg-gray-900 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              How It Works
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '01', title: 'Create Account', desc: 'Sign up with your email and password. Your data stays private.' },
              { step: '02', title: 'Add API Keys', desc: 'Bring your own Gemini, OpenRouter, NVIDIA, or Ollama keys.' },
              { step: '03', title: 'Upload Resume', desc: 'Paste your master LaTeX resume or upload a file.' },
              { step: '04', title: 'Generate & Download', desc: 'Paste a JD, get a tailored PDF + .tex in seconds.' },
            ].map((item, i) => (
              <div key={i} className="relative text-center">
                <div className="h-16 w-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mx-auto mb-4 text-2xl font-bold text-primary-600 dark:text-primary-400">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  {item.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 text-sm">{item.desc}</p>
                {i < 3 && (
                  <div className="absolute top-8 right-0 w-full h-0.5 bg-gray-200 dark:bg-gray-700 hidden md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="card p-8 sm:p-12 bg-primary-600 border-primary-600">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Ready to Tailor Your Resume?
            </h2>
            <p className="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
              Join thousands of job seekers who are getting more interviews with AI-tailored resumes.
              Free to start, no credit card required.
            </p>
            <Link href="/login" className="btn bg-white text-primary-600 hover:bg-primary-50 text-lg px-8 py-3">
              Get Started Free
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <FileText className="h-6 w-6 text-primary-600" />
              <span className="text-lg font-semibold text-gray-900 dark:text-white">JD Resume Changer</span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Built for job seekers who want honest, ATS-optimized resumes.
            </p>
            <div className="flex items-center gap-6">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <Github className="h-5 w-5" />
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}