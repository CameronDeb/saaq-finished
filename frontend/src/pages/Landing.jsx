import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import Logo from '../components/Logo'

export default function Landing() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth()
  const navigate = useNavigate()
  const [prices, setPrices] = useState(null)
  const [loadingCheckout, setLoadingCheckout] = useState(null)

  const [grant, setGrant] = useState(null)

  useEffect(() => {
    api.getPricing().then(res => setPrices(res.prices)).catch(() => {})
    if (isAuthenticated) {
      api.checkGrant().then(res => { if (res.has_grant) setGrant(res) }).catch(() => {})
    }
  }, [isAuthenticated])

  const handleCheckout = async (productType) => {
    if (!isAuthenticated) {
      navigate('/signup', { state: { from: '/' } })
      return
    }
    // check if user has a free grant
    if (grant?.has_grant) {
      try {
        await api.redeemGrant(grant.grant_id)
        const version = grant.product_type?.startsWith('30q') ? '30Q' : '15Q'
        navigate(`/assessment/${version}`)
        return
      } catch {}
    }
    setLoadingCheckout(productType)
    try {
      const result = await api.createCheckout(productType)
      window.location.href = result.checkout_url
    } catch (err) { alert(err.message) }
    finally { setLoadingCheckout(null) }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* nav */}
      <nav className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size={40} />
            <span className="text-lg font-bold text-gray-800">SkillfullyAware</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <a href="#how-it-works" className="text-gray-600 hover:text-gray-800 hidden md:inline">How It Works</a>
            <a href="#pricing" className="text-gray-600 hover:text-gray-800 hidden md:inline">Pricing</a>
            {isAuthenticated ? (
              <>
                {isAdmin && <Link to="/dashboard" className="text-gray-600 hover:text-gray-800">Admin</Link>}
                <Link to="/my" className="text-gray-600 hover:text-gray-800">My Account</Link>
                <button onClick={logout} className="text-gray-400 hover:text-gray-600">Sign out</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 hover:text-gray-800">Sign in</Link>
                <Link to="/signup" className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition">
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* hero */}
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-12 text-center">
        <h1 className="text-3xl md:text-5xl font-bold text-gray-800 mb-6 leading-tight">
          See the Patterns That Shape How You Lead, Relate, and Grow
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
          Created by Dr. Mark Pirtle, the SAAQ helps high-performing leaders and growth-oriented people
          identify the patterns that shape how they lead, relate, make decisions, and respond under pressure.
          Rooted in Mark's SkillfullyAware approach, each report turns deep self-awareness into practical
          next steps for better conversations, clearer leadership, and meaningful behavior change.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <a href="#pricing" className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition">
            Choose Your SAAQ Path
          </a>
          <a href="https://www.drmarkpirtle.com/"
            className="border-2 border-gray-300 text-gray-700 px-8 py-3 rounded-lg text-lg font-medium hover:border-gray-400 transition">
            Schedule a Conversation with Mark
          </a>
        </div>
      </section>

      {/* credibility band */}
      <section className="bg-white border-y">
        <div className="max-w-3xl mx-auto px-6 py-10 text-center">
          <p className="text-xs uppercase tracking-widest text-gray-400 mb-3">Created by</p>
          <h2 className="text-xl font-bold text-gray-800 mb-3">Dr. Mark Pirtle</h2>
          <p className="text-gray-500 max-w-xl mx-auto text-sm leading-relaxed">
            Mark is a retreat leader, author, speaker, and creator of the SkillfullyAware approach.
            His work integrates mindfulness, developmental psychology, shadow work, and practical behavior
            change to help people see themselves more clearly and grow with greater skillful awareness.
          </p>
        </div>
      </section>

      {/* what the SAAQ helps you see */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-3">What the SAAQ helps you see</h2>
        <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10">
          Your personalized report provides a comprehensive developmental snapshot across six dimensions,
          giving you clarity on where you are, where you're growing, and what to do next.
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { title: 'Developmental Stage', desc: 'See your current center of gravity, growth edge, and common stress patterns across the S1-S10 developmental continuum.' },
            { title: 'Power Center Analysis', desc: 'Understand how your awareness expresses across eight life domains: physical vitality, emotional life, relationships, social leadership, finances, creativity, intellect, and spirituality.' },
            { title: 'Shadow Indicators', desc: 'Identify recurring stress loops, hidden patterns, and practical ways to interrupt them.' },
            { title: 'Core Aptitudes', desc: 'Explore the leadership and life capacities that shape how you act, relate, reflect, and regulate yourself.' },
            { title: '90-Day Practice Plan', desc: 'Translate insight into weekly practices, simple commitments, and measurable next steps.' },
            { title: 'Coach / Therapist Summary', desc: 'A concise summary you can share with a coach, therapist, or trusted advisor to focus your growth work.' },
          ].map(item => (
            <div key={item.title} className="bg-white rounded-xl border p-6">
              <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* how it works */}
      <section id="how-it-works" className="bg-white border-y">
        <div className="max-w-4xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-gray-800 text-center mb-10">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: '1', title: 'Complete the assessment', desc: 'Answer reflective questions about how you lead, relate, respond, and grow.' },
              { step: '2', title: 'Receive your report', desc: 'Get a personalized developmental profile with strengths, blind spots, and growth opportunities.' },
              { step: '3', title: 'Review your practice plan', desc: 'Use the 90-day plan to turn insight into action.' },
              { step: '4', title: 'Optional debrief or retreat', desc: 'Work with Mark individually, with your forum, or with your leadership team.' },
            ].map(item => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* forums and teams */}
      <section className="max-w-3xl mx-auto px-6 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">For Forums, Leadership Teams, and Growth-Oriented Groups</h2>
        <p className="text-gray-500 max-w-2xl mx-auto mb-8 leading-relaxed">
          The SAAQ can also be used as the foundation for a facilitated retreat or team development experience.
          Each participant completes the assessment, receives a personalized report, and comes prepared for a
          deeper conversation about leadership, stress patterns, communication, trust, and next-stage growth.
        </p>
        <a href="https://www.drmarkpirtle.com/"
          className="bg-gray-800 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-900 transition inline-block">
          Explore a SAAQ Retreat
        </a>
      </section>

      {/* trust signals */}
      <section className="bg-white border-y">
        <div className="max-w-4xl mx-auto px-6 py-10">
          <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-sm text-gray-500">
            <span>Seasoned retreat leader</span>
            <span className="text-gray-300">|</span>
            <span>Author and speaker</span>
            <span className="text-gray-300">|</span>
            <span>Creator of the SkillfullyAware approach</span>
            <span className="text-gray-300">|</span>
            <span>Used with EO forum participants</span>
            <span className="text-gray-300">|</span>
            <span>Rooted in developmental psychology</span>
          </div>
        </div>
      </section>

      {/* pricing */}
      <section id="pricing" className="max-w-4xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-3">Choose Your Path</h2>
        <p className="text-gray-500 text-center mb-10">Select the option that fits where you are right now.</p>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Report Only */}
          <div className="bg-white rounded-2xl border p-8 flex flex-col">
            <h3 className="text-lg font-bold text-gray-800 mb-2">SAAQ Report Only</h3>
            <p className="text-sm text-gray-500 mb-4 flex-1">
              The full personalized report and 90-day practice plan.
            </p>
            <p className="text-3xl font-bold text-gray-800 mb-6">
              ${prices?.['30q_report']?.amount || 500}
            </p>
            <button
              onClick={() => handleCheckout('30q_report')}
              disabled={loadingCheckout === '30q_report'}
              className="w-full bg-gray-800 text-white py-3 rounded-lg font-medium hover:bg-gray-900 disabled:opacity-50 transition"
            >
              {loadingCheckout === '30q_report' ? 'Loading...' : 'Select'}
            </button>
          </div>

          {/* Report + Sessions */}
          <div className="bg-white rounded-2xl border-2 border-blue-200 p-8 flex flex-col relative">
            <span className="absolute -top-3 left-6 bg-blue-600 text-white text-xs font-medium px-3 py-1 rounded-full">Most Popular</span>
            <h3 className="text-lg font-bold text-gray-800 mb-2">SAAQ Report + Debrief</h3>
            <p className="text-sm text-gray-500 mb-4 flex-1">
              The full report plus two private sessions with Mark to interpret findings and identify next steps.
            </p>
            <p className="text-3xl font-bold text-blue-600 mb-6">
              ${prices?.['30q_bundle']?.amount || 1000}
            </p>
            <button
              onClick={() => handleCheckout('30q_bundle')}
              disabled={loadingCheckout === '30q_bundle'}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {loadingCheckout === '30q_bundle' ? 'Loading...' : 'Select'}
            </button>
          </div>

          {/* Forum/Team */}
          <div className="bg-white rounded-2xl border p-8 flex flex-col">
            <h3 className="text-lg font-bold text-gray-800 mb-2">Forum or Team Retreat</h3>
            <p className="text-sm text-gray-500 mb-4 flex-1">
              For forums, leadership teams, and groups that want the SAAQ as part of a facilitated retreat or offsite.
            </p>
            <p className="text-3xl font-bold text-gray-800 mb-6">Custom</p>
            <a
              href="https://www.drmarkpirtle.com/"
              className="w-full bg-gray-800 text-white py-3 rounded-lg font-medium hover:bg-gray-900 transition text-center block"
            >
              Schedule a Conversation
            </a>
          </div>
        </div>
      </section>

      {/* voice tip - small and subtle */}
      <section className="max-w-2xl mx-auto px-6 pb-8">
        <details className="bg-blue-50 border border-blue-200 rounded-xl p-4 cursor-pointer">
          <summary className="text-sm font-medium text-blue-800">
            Prefer to speak your answers?
          </summary>
          <p className="text-xs text-blue-700 mt-3 leading-relaxed">
            You can use voice dictation on most devices. This often helps people answer more naturally and completely.
          </p>
          <ul className="text-xs text-blue-600 mt-2 space-y-1">
            <li>iPhone / iPad: tap the microphone icon on your keyboard</li>
            <li>Mac: press the Fn key twice</li>
            <li>Windows: press Win + H</li>
            <li>Android: tap the microphone icon on your keyboard</li>
          </ul>
        </details>
      </section>

      {/* final CTA */}
      <section className="bg-gray-800 text-white">
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to see yourself more clearly?</h2>
          <p className="text-gray-300 mb-8 max-w-xl mx-auto">
            Choose the individual SAAQ path above, or schedule a conversation with Mark about bringing
            the SAAQ to your forum, team, or retreat.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a href="#pricing" className="bg-white text-gray-800 px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-100 transition">
              Choose My SAAQ Path
            </a>
            <a href="https://www.drmarkpirtle.com/"
              className="border-2 border-white text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-white hover:text-gray-800 transition">
              Schedule a Conversation
            </a>
          </div>
        </div>
      </section>

      {/* footer */}
      <footer className="border-t py-8 text-center text-sm text-gray-400">
        <p>&copy; {new Date().getFullYear()} SkillfullyAware. All rights reserved.</p>
      </footer>
    </div>
  )
}