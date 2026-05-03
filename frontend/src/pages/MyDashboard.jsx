import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import Logo from '../components/Logo'

export default function MyDashboard() {
  const { user, logout } = useAuth()
  const [intakes, setIntakes] = useState([])
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [intakeRes, reportRes] = await Promise.all([api.myIntakes(), api.myReports()])
      setIntakes(intakeRes.intakes || [])
      setReports(reportRes.reports || [])
    } catch (err) {
      console.error('Failed to load data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (intakeId, name) => {
    try {
      const blob = await api.downloadReport(intakeId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `SAAQReport-${name}.docx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Report not ready yet. Please check back later.')
    }
  }

  const getReportForIntake = (intakeId) => reports.find(r => r.intake_id === intakeId)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/"><Logo size={36} /></Link>
            <span className="text-lg font-semibold text-gray-800">My Account</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-500">{user?.email}</span>
            {user?.role === 'admin' && (
              <Link to="/dashboard" className="text-sm text-blue-600 hover:underline">Admin</Link>
            )}
            <button onClick={logout} className="text-sm text-gray-400 hover:text-gray-600">Sign out</button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Welcome, {user?.full_name || user?.email}</h1>
        <p className="text-gray-500 mb-8">View your assessments and download reports.</p>

        {loading ? (
          <p className="text-gray-400">Loading...</p>
        ) : intakes.length === 0 ? (
          <div className="bg-white rounded-xl border p-8 text-center">
            <p className="text-gray-500 mb-4">You haven't taken any assessments yet.</p>
            <Link to="/" className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition">
              Take an assessment
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {intakes.map(intake => {
              const report = getReportForIntake(intake.id)
              const status = report?.status || intake.status || 'pending'
              return (
                <div key={intake.id} className="bg-white rounded-xl border p-6 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-800">{intake.first_name} - {intake.version} Assessment</p>
                    <p className="text-sm text-gray-400">{new Date(intake.submitted_at).toLocaleDateString()}</p>
                    <span className={`inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full ${
                      status === 'complete' ? 'bg-green-100 text-green-700' :
                      status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>
                      {status}
                    </span>
                  </div>
                  {status === 'complete' && (
                    <button
                      onClick={() => handleDownload(intake.id, intake.first_name)}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition"
                    >
                      Download Report
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
