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

  useEffect(() => {
    api.getPricing().then(res => setPrices(res.prices)).catch(() => {})
  }, [])

  const handleCheckout = async (productType) => {
    if (!isAuthenticated) {
      navigate('/signup', { state: { from: '/' } })
      return
    }
    setLoadingCheckout(productType)
    try {
      const result = await api.createCheckout(productType)
      window.location.href = result.checkout_url
    } catch (err) {
      alert(err.message)
    } finally {
      setLoadingCheckout(null)
    }
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
          <div className="flex items-center gap-4">
            <a href="#pricing" className="text-sm text-gray-600 hover:text-gray-800">Pricing</a>
            {isAuthenticated ? (
              <>
                {isAdmin && <Link to="/dashboard" className="text-sm text-gray-600 hover:text-gray-800">Admin</Link>}
                <Link to="/my" className="text-sm text-gray-600 hover:text-gray-800">My Account</Link>
                <button onClick={logout} className="text-sm text-gray-400 hover:text-gray-600">Sign out</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-gray-600 hover:text-gray-800">Sign in</Link>
                <Link to="/signup" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                  Get started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* hero */}
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-12 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4 leading-tight">
          Discover your developmental edge
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
          The SAAQ assessment provides a comprehensive, strengths-forward developmental snapshot
          to help you grow as a leader and a person. Receive a personalized 12-section diagnostic
          report with actionable insights and a 90-day practice plan.
        </p>
        <a href="#pricing" className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-blue-700 transition">
          Choose your assessment
        </a>
      </section>

      {/* what you get */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-8">What's in your report</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { title: 'Developmental Stage', desc: 'Your center of gravity, leading edge, and stress patterns on the S1-S10 continuum.' },
            { title: 'Power Center Analysis', desc: '8 dimensions assessed: Physical, Emotional, Relational, Social, Financial, Creative, Intellectual, Spiritual.' },
            { title: 'Shadow Indicators', desc: 'Your recurring stress loops identified with specific antidotes and practices.' },
            { title: 'Core Aptitudes', desc: '7 leadership capacities assessed: Agency through Restraint.' },
            { title: '90-Day Practice Plan', desc: 'Weekly cadence, daily minimums, if-then protocols, and measurable milestones.' },
            { title: 'Therapist Handoff', desc: 'A clinical summary your therapist or coach can use to focus sessions immediately.' },
          ].map(item => (
            <div key={item.title} className="bg-white rounded-xl border p-5">
              <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
              <p className="text-sm text-gray-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* pricing */}
      <section id="pricing" className="max-w-5xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-gray-800 text-center mb-3">Choose your path</h2>
        <p className="text-gray-500 text-center mb-10">Select the assessment and service level that fits your needs.</p>

        <div className="grid md:grid-cols-2 gap-8">
          {/* 15Q */}
          <div className="bg-white rounded-2xl border p-8">
            <h3 className="text-xl font-bold text-gray-800 mb-2">15-Question Assessment</h3>
            <p className="text-sm text-gray-500 mb-6">A focused snapshot of your developmental patterns.</p>
            <div className="space-y-4 mb-8">
              <PricingOption
                label={prices?.['15q_report']?.label || '15-Question Report Only'}
                price={prices?.['15q_report']?.amount || 400}
                loading={loadingCheckout === '15q_report'}
                onClick={() => handleCheckout('15q_report')}
              />
              <PricingOption
                label={prices?.['15q_bundle']?.label || '15-Question Report + Sessions'}
                price={prices?.['15q_bundle']?.amount || 1000}
                featured
                loading={loadingCheckout === '15q_bundle'}
                onClick={() => handleCheckout('15q_bundle')}
              />
            </div>
          </div>

          {/* 30Q */}
          <div className="bg-white rounded-2xl border-2 border-blue-200 p-8 relative">
            <span className="absolute -top-3 left-6 bg-blue-600 text-white text-xs font-medium px-3 py-1 rounded-full">Recommended</span>
            <h3 className="text-xl font-bold text-gray-800 mb-2">30-Question Deep Dive</h3>
            <p className="text-sm text-gray-500 mb-6">The most comprehensive developmental assessment available.</p>
            <div className="space-y-4 mb-8">
              <PricingOption
                label={prices?.['30q_report']?.label || '30-Question Report Only'}
                price={prices?.['30q_report']?.amount || 400}
                loading={loadingCheckout === '30q_report'}
                onClick={() => handleCheckout('30q_report')}
              />
              <PricingOption
                label={prices?.['30q_bundle']?.label || '30-Question Report + Sessions'}
                price={prices?.['30q_bundle']?.amount || 1000}
                featured
                loading={loadingCheckout === '30q_bundle'}
                onClick={() => handleCheckout('30q_bundle')}
              />
            </div>
          </div>
        </div>

        {/* voice tip */}
        <div className="mt-10 bg-blue-50 border border-blue-200 rounded-xl p-6 max-w-2xl mx-auto">
          <p className="text-sm font-medium text-blue-800 mb-2">Tip: You can speak your answers</p>
          <p className="text-xs text-blue-700">
            iPhone/iPad: tap the mic icon on your keyboard. Mac: press Fn twice. Windows: press Win+H. Android: tap the mic icon.
          </p>
        </div>
      </section>

      {/* footer */}
      <footer className="border-t py-8 text-center text-sm text-gray-400">
        <p>&copy; {new Date().getFullYear()} SkillfullyAware. All rights reserved.</p>
      </footer>
    </div>
  )
}

function PricingOption({ label, price, featured, loading, onClick }) {
  return (
    <div className={`flex items-center justify-between p-4 rounded-xl border ${featured ? 'border-blue-200 bg-blue-50' : 'border-gray-200'}`}>
      <div>
        <p className={`font-medium ${featured ? 'text-blue-800' : 'text-gray-800'}`}>{label}</p>
        <p className={`text-2xl font-bold ${featured ? 'text-blue-600' : 'text-gray-800'}`}>${price}</p>
      </div>
      <button
        onClick={onClick} disabled={loading}
        className={`px-5 py-2.5 rounded-lg text-sm font-medium transition ${
          featured
            ? 'bg-blue-600 text-white hover:bg-blue-700'
            : 'bg-gray-800 text-white hover:bg-gray-900'
        } disabled:opacity-50`}
      >
        {loading ? 'Loading...' : 'Select'}
      </button>
    </div>
  )
}
