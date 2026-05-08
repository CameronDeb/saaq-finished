import { Link, useLocation } from 'react-router-dom'
import Logo from '../components/Logo'

export default function ThankYou() {
  const location = useLocation()
  const name = location.state?.name || 'there'

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div className="flex justify-center mb-6">
          <Link to="/"><Logo size={56} /></Link>
        </div>

        <h1 className="text-3xl font-bold text-gray-800 mb-4">
          Thank you, {name}.
        </h1>

        <p className="text-gray-500 mb-8 leading-relaxed">
          Your responses have been received. Your personalized SAAQ Diagnostic Report
          is being prepared and will include your developmental stage assessment,
          power center analysis, shadow indicators, and a 90-day growth plan.
        </p>

        <div className="bg-blue-50 rounded-xl p-5 mb-8 text-left">
          <p className="font-semibold text-gray-700 mb-3">What happens next?</p>
          <ul className="text-sm text-gray-500 space-y-2">
            <li>&#8594; Your responses are analyzed using our developmental framework</li>
            <li>&#8594; A comprehensive 12-section report is generated</li>
            <li>&#8594; You'll receive your report within 24 hours</li>
          </ul>
        </div>

        <div className="flex flex-col gap-3">
          <Link to="/my" className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
            View My Account
          </Link>
          <Link to="/" className="text-blue-600 hover:underline text-sm">
            &#8592; Return home
          </Link>
        </div>
      </div>
    </div>
  )
}