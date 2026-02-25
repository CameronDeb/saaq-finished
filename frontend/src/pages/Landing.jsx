import { Link } from 'react-router-dom'
import Logo from '../components/Logo'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-sa-700 via-sa-800 to-sa-900 flex flex-col">
      {/* Nav */}
      <nav className="px-6 py-4 flex justify-between items-center max-w-6xl mx-auto w-full">
        <div className="flex items-center gap-3">
          <Logo size={40} />
          <span className="text-white font-display text-lg font-semibold tracking-wide">
            SkillfullyAware
          </span>
        </div>
        <Link to="/dashboard" className="text-sa-200 hover:text-white text-sm transition">
          Admin
        </Link>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="max-w-2xl text-center">
          <div className="flex justify-center mb-8">
            <Logo size={96} />
          </div>

          <p className="text-sa-300 uppercase tracking-widest text-xs font-semibold mb-3">
            Dr. Mark Pirtle
          </p>

          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
            Awareness Quotient
          </h1>
          <p className="text-sa-200 text-lg md:text-xl leading-relaxed mb-4">
            A whole-person snapshot of how you relate to yourself, others, and the world — right now.
          </p>
          <p className="text-sa-300 text-base leading-relaxed mb-10 max-w-lg mx-auto">
            This reflective assessment takes 15–30 minutes. There are no right or wrong answers.
            Your honest, thoughtful responses will generate a personalized developmental report
            with practical insights and a 90-day growth plan.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/assessment/15Q"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-sa-700 font-semibold rounded-xl hover:bg-sa-50 transition shadow-lg hover:shadow-xl text-lg"
            >
              Begin Assessment
              <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>

          <p className="text-sa-400 text-xs mt-8">
            Your responses are confidential and used only to generate your personal report.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-6 text-center text-sa-400 text-sm">
        <div className="flex items-center justify-center gap-2">
          <Logo size={20} />
          <span>© 2026 SkillfullyAware · Dr. Mark Pirtle</span>
        </div>
      </footer>
    </div>
  )
}
