import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Logo from '../components/Logo'

export default function PaymentSuccess() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('verifying')
  const [productType, setProductType] = useState(null)
  const sessionId = searchParams.get('session_id')

  useEffect(() => {
    if (!sessionId) { setStatus('error'); return }

    const verify = async () => {
      try {
        const result = await api.verifyPayment(sessionId)
        if (result.status === 'completed') {
          setStatus('success')
          setProductType(result.product_type)
          // store payment info for intake form
          localStorage.setItem('saaq_payment', JSON.stringify({
            payment_id: result.payment_id,
            product_type: result.product_type,
            session_id: sessionId,
          }))
          // auto-redirect to assessment after 3 seconds
          const version = result.product_type?.startsWith('30q') ? '30Q' : '15Q'
          setTimeout(() => navigate(`/assessment/${version}`), 3000)
        } else {
          setStatus('pending')
        }
      } catch {
        setStatus('error')
      }
    }
    verify()
  }, [sessionId, navigate])

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div className="flex justify-center mb-6"><Logo size={56} /></div>

        {status === 'verifying' && (
          <>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Verifying payment...</h1>
            <p className="text-gray-500">Please wait a moment.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="text-5xl mb-4">&#10003;</div>
            <h1 className="text-2xl font-bold text-green-700 mb-4">Payment successful!</h1>
            <p className="text-gray-600 mb-6">
              Thank you for your purchase. You'll be redirected to your assessment in a moment.
            </p>
            <button
              onClick={() => navigate(`/assessment/${productType?.startsWith('30q') ? '30Q' : '15Q'}`)}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Start assessment now
            </button>
          </>
        )}

        {status === 'pending' && (
          <>
            <h1 className="text-2xl font-bold text-yellow-700 mb-4">Payment processing...</h1>
            <p className="text-gray-600">Your payment is still being processed. Please check back in a minute.</p>
          </>
        )}

        {status === 'error' && (
          <>
            <h1 className="text-2xl font-bold text-red-700 mb-4">Something went wrong</h1>
            <p className="text-gray-600 mb-6">We couldn't verify your payment. Please contact support.</p>
            <button onClick={() => navigate('/')} className="text-blue-600 hover:underline">Return home</button>
          </>
        )}
      </div>
    </div>
  )
}
