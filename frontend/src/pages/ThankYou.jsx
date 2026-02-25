import { Link, useLocation } from 'react-router-dom'
import Logo from '../components/Logo'

export default function ThankYou() {
  const location = useLocation()
  const name = location.state?.name || 'there'
  const offline = location.state?.offline

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-lg text-center">
        <div className="flex justify-center mb-6">
          <Logo size={72} />
        </div>

        <h1 className="font-display text-3xl md:text-4xl font-bold text-sa-700 mb-4">
          Thank you, {name}.
        </h1>

        <p className="text-gray-600 text-lg leading-relaxed mb-6">
          Your responses have been received. Your personalized SAAQ Diagnostic Report
          is being prepared and will include your developmental stage assessment,
          power center analysis, shadow indicators, and a 90-day growth plan.
        </p>

        {offline && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6 text-sm text-amber-800">
            Your responses were saved locally. They'll be submitted automatically when the connection is restored.
          </div>
        )}

        <div className="bg-sa-50 rounded-xl p-6 mb-8 text-left">
          <h3 className="font-semibold text-sa-700 mb-3">What happens next?</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <p>→ Your responses are analyzed using our developmental framework</p>
            <p>→ A comprehensive 12-section report is generated</p>
            <p>→ You'll receive your report within 24 hours</p>
          </div>
        </div>

        <Link
          to="/"
          className="inline-flex items-center text-sa-600 hover:text-sa-700 font-medium transition"
        >
          <svg className="mr-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Return home
        </Link>
      </div>
    </div>
  )
}
