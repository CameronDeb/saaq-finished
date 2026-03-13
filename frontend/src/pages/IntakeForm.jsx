import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Logo from '../components/Logo'

const QUESTIONS_15Q = [
  "Describe a recent challenge. What happened, and how did you deal with it?",
  "When you're overwhelmed or afraid, what happens in your body, and how does it show up in your behavior?",
  "Looking back, how has your understanding of yourself and the world changed most over the years?",
  "Tell us about a time when you felt misunderstood. How did you handle it, and what did you learn?",
  "Tell us about a time when your values were tested. What did you discover about yourself?",
  "Can you describe a moment when you felt pulled between two opposing values, impulses, or desires? How did you navigate that conflict?",
  "What do you notice about your inner voice or self-talk? How do you relate to it?",
  "How do you typically process emotions\u2014your own and others'? Have strong feelings ever clouded your clarity?",
  "In groups, what role do you most often play? How do others tend to experience you?",
  "How do you stay open to people with very different views? What helps you stay connected?",
  "What really gets under your skin about other people? What do you most admire?",
  "How do you relate to your body and energy right now? Has this changed over time?",
  "What is money, and how do you relate to it? What habits, emotions, or stories come up around earning, spending, saving, or investing?",
  "What role do creativity and imagination play in your life? How do you express them?",
  "How do you understand or connect with something larger than yourself (God, spirit, Universe)?",
]

const QUESTIONS_30Q = [
  "Describe a recent challenge. What happened, and how did you deal with it?",
  "When you're overwhelmed or afraid, what happens in your body, and how does it show up in your behavior?",
  "Looking back, how has your understanding of yourself and the world changed most over the years?",
  "Tell us about a time when you felt misunderstood. How did you handle it, and what did you learn?",
  "Tell us about a time when your values were tested. What did you discover about yourself?",
  "Can you describe a moment when you felt pulled between two opposing values, impulses, or desires? How did you navigate that conflict?",
  "What do you notice about your inner voice or self-talk? How do you relate to it?",
  "How do you typically process emotions\u2014your own and others'? Have strong feelings ever clouded your clarity?",
  "In groups, what role do you most often play? How do others tend to experience you?",
  "How do you stay open to people with very different views? What helps you stay connected?",
  "What really gets under your skin about other people? What do you most admire?",
  "Tell us about a relationship that deeply shaped you\u2014for better or worse. How did you respond, and what did you learn?",
  "How do you relate to your body and energy right now? Has this changed over time?",
  "What is money?",
  "How do you relate to money? What habits, emotions, or stories come up around earning, spending, saving, or investing?",
  "What is time?",
  "How do you relate to time? What habits, emotions, or stories come up around your experience of time?",
  "What role do creativity and imagination play in your life? How do you express them?",
  "How do you understand or connect with something larger than yourself (God, spirit, Universe)?",
  "When you've been involved in a group or community, what role did you naturally play?",
  "How do you challenge your own thinking? Tell us about a person, idea, book, insight, or experience that challenged and stretched your perspective.",
  "Tell us about a time when you followed through on something difficult. What drove you?",
  "Tell us about a time when you had to hold back \u2014 when restraint mattered more than action.",
  "Tell us about a time when you could have taken advantage of a situation but chose not to. What guided your choice?",
  "When it comes to tasks and commitments, how do you balance thoroughness with efficiency?",
  "Think of a time when you influenced others without relying on authority. How did you gain their trust or move them toward action?",
  "What gives your life meaning? Has that sense of purpose changed over the years?",
  "When you face setbacks, what does your self-talk sound like?",
  "How do you respond when someone disappoints you or doesn't meet your expectations?",
  "What kinds of new ventures, ideas, art, or experiences most inspire or stretch you?",
]

export default function IntakeForm() {
  const { version = '15Q' } = useParams()
  const navigate = useNavigate()
  const textareaRef = useRef(null)

  const questions = version === '30Q' ? QUESTIONS_30Q : QUESTIONS_15Q
  const [step, setStep] = useState(-1) // -1 = name/email, 0+ = questions
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [answers, setAnswers] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (step >= 0 && textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [step])

  const progress = step < 0 ? 0 : ((step + 1) / questions.length) * 100

  const handleNext = () => {
    if (step === -1) {
      if (!name.trim()) { setError('Please enter your first name'); return }
      setError('')
      setStep(0)
    } else if (step < questions.length - 1) {
      if (!answers[questions[step]]?.trim()) { setError('Please share your thoughts before continuing'); return }
      setError('')
      setStep(step + 1)
    }
  }

  const handleBack = () => {
    setError('')
    if (step > -1) setStep(step - 1)
  }

  const handleSubmit = async () => {
    if (!answers[questions[step]]?.trim()) { setError('Please share your thoughts before submitting'); return }
    setSubmitting(true)
    setError('')

    try {
      const payload = {
        first_name: name.trim(),
        email: email.trim() || null,
        version: version,
        responses: answers,
      }

      await api.submitIntake(payload)
      navigate('/thank-you', { state: { name: name.trim() } })
    } catch (err) {
      console.error('Submit failed:', err)
      localStorage.setItem('saaq_pending_submission', JSON.stringify({
        first_name: name.trim(),
        email: email.trim(),
        version,
        responses: answers,
        submitted_at: new Date().toISOString(),
      }))
      navigate('/thank-you', { state: { name: name.trim(), offline: true } })
    }
  }

  const isLastQuestion = step === questions.length - 1

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-2xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Logo size={28} />
            <span className="font-display text-sa-700 text-lg font-semibold">SAAQ</span>
            <span className="text-xs text-gray-400 ml-1">{version}</span>
          </div>
          {step >= 0 && (
            <div className="text-sm text-gray-500">
              {step + 1} of {questions.length}
            </div>
          )}
        </div>
      </header>

      {/* Progress bar */}
      {step >= 0 && (
        <div className="bg-gray-200 h-1">
          <div
            className="bg-sa-600 h-1 transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Content */}
      <main className="flex-1 flex items-start justify-center px-6 py-8 md:py-16">
        <div className="w-full max-w-2xl">
          {step === -1 ? (
            /* Name/Email Step */
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 md:p-12">
              <h2 className="font-display text-2xl md:text-3xl font-semibold text-sa-700 mb-2">
                Welcome
              </h2>
              <p className="text-gray-500 mb-8">
                Before we begin, please tell us your name. This will be used to personalize your report.
                {version === '30Q' && (
                  <span className="block mt-2 text-sm text-sa-600">
                    You're taking the extended {questions.length}-question assessment.
                  </span>
                )}
              </p>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">First Name *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                    placeholder="Your first name"
                    autoFocus
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sa-500 focus:border-sa-500 outline-none transition text-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Email (optional)</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                    placeholder="your@email.com"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sa-500 focus:border-sa-500 outline-none transition"
                  />
                  <p className="text-xs text-gray-400 mt-1">We'll send your report here when it's ready.</p>
                </div>
              </div>

              {error && <p className="text-red-500 text-sm mt-4">{error}</p>}

              <button
                onClick={handleNext}
                className="mt-8 w-full py-4 bg-sa-700 text-white font-semibold rounded-xl hover:bg-sa-800 transition text-lg"
              >
                Start Assessment
              </button>
            </div>
          ) : (
            /* Question Step */
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 md:p-12">
              <div className="mb-6">
                <span className="inline-block bg-sa-50 text-sa-600 text-xs font-semibold px-3 py-1 rounded-full mb-4">
                  Question {step + 1}
                </span>
                <h2 className="font-display text-xl md:text-2xl font-semibold text-gray-900 leading-snug">
                  {questions[step]}
                </h2>
              </div>

              <textarea
                ref={textareaRef}
                value={answers[questions[step]] || ''}
                onChange={(e) => setAnswers({ ...answers, [questions[step]]: e.target.value })}
                placeholder="Take your time. There are no right or wrong answers..."
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-sa-500 focus:border-sa-500 outline-none transition text-base leading-relaxed"
              />

              <p className="text-xs text-gray-400 mt-2">
                Write as much or as little as you'd like. Richer responses produce more personalized reports.
              </p>

              {error && <p className="text-red-500 text-sm mt-4">{error}</p>}

              <div className="flex justify-between mt-8">
                <button
                  onClick={handleBack}
                  className="px-6 py-3 text-gray-600 hover:text-gray-900 font-medium transition"
                >
                  ← Back
                </button>

                {isLastQuestion ? (
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="px-8 py-3 bg-sa-700 text-white font-semibold rounded-xl hover:bg-sa-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? 'Submitting...' : 'Submit Assessment'}
                  </button>
                ) : (
                  <button
                    onClick={handleNext}
                    className="px-8 py-3 bg-sa-700 text-white font-semibold rounded-xl hover:bg-sa-800 transition"
                  >
                    Continue →
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}