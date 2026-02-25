import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Logo from '../components/Logo'

function StatusBadge({ status }) {
  const styles = {
    pending: 'bg-yellow-100 text-yellow-700',
    analyzing: 'bg-blue-100 text-blue-700',
    generating: 'bg-purple-100 text-purple-700',
    complete: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

export default function Dashboard() {
  const [intakes, setIntakes] = useState([])
  const [reports, setReports] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [generating, setGenerating] = useState(new Set())

  const load = async () => {
    try {
      const [intakeRes, reportRes, healthRes] = await Promise.all([
        api.listIntakes().catch(() => ({ intakes: [] })),
        api.listReports().catch(() => ({ reports: [] })),
        api.health().catch(() => null),
      ])
      setIntakes(intakeRes.intakes || [])
      setReports(reportRes.reports || [])
      setHealth(healthRes)
      setError('')
    } catch (err) {
      setError('Failed to connect to backend. Is it running?')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleGenerate = async (intakeId) => {
    setGenerating(prev => new Set([...prev, intakeId]))
    try {
      await api.generateReport(intakeId)
      // Poll for completion
      const poll = setInterval(async () => {
        const report = await api.getReport(intakeId)
        if (report.status === 'complete' || report.status === 'failed') {
          clearInterval(poll)
          setGenerating(prev => { const s = new Set(prev); s.delete(intakeId); return s })
          load()
        }
      }, 3000)
    } catch (err) {
      setError(err.message)
      setGenerating(prev => { const s = new Set(prev); s.delete(intakeId); return s })
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
      setError(err.message)
    }
  }

  const getReportForIntake = (intakeId) =>
    reports.find(r => r.intake_id === intakeId)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size={32} />
            <div>
              <span className="font-display text-sa-700 text-lg font-semibold">SAAQ</span>
              <span className="text-gray-400 text-sm ml-2">Admin Dashboard</span>
            </div>
          </div>
          <Link to="/" className="text-sm text-gray-500 hover:text-sa-600 transition">
            ← Back to site
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Status bar */}
        {health && (
          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health.api_key_configured ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-gray-600">API Key {health.api_key_configured ? 'Active' : 'Missing'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health.pipeline_available ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-gray-600">DOCX Pipeline {health.pipeline_available ? 'Ready' : 'Not Found'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health.database_configured ? 'bg-green-500' : 'bg-yellow-500'}`} />
              <span className="text-gray-600">{health.database_configured ? 'Supabase' : 'In-Memory DB'}</span>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-6 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="text-2xl font-bold text-sa-700">{intakes.length}</div>
            <div className="text-sm text-gray-500">Total Submissions</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="text-2xl font-bold text-green-600">
              {reports.filter(r => r.status === 'complete').length}
            </div>
            <div className="text-sm text-gray-500">Reports Complete</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="text-2xl font-bold text-yellow-600">
              {intakes.filter(i => !getReportForIntake(i.id)).length}
            </div>
            <div className="text-sm text-gray-500">Pending</div>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="text-2xl font-bold text-red-600">
              {reports.filter(r => r.status === 'failed').length}
            </div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
        </div>

        {/* Intakes Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="font-semibold text-gray-900">Submissions</h2>
            <button
              onClick={load}
              className="text-sm text-sa-600 hover:text-sa-700 font-medium"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="px-6 py-12 text-center text-gray-400">Loading...</div>
          ) : intakes.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-400">
              No submissions yet. Share the assessment link to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <th className="px-6 py-3">Name</th>
                    <th className="px-6 py-3">Version</th>
                    <th className="px-6 py-3">Responses</th>
                    <th className="px-6 py-3">Status</th>
                    <th className="px-6 py-3">Submitted</th>
                    <th className="px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {intakes.map((intake) => {
                    const report = getReportForIntake(intake.id)
                    const isGenerating = generating.has(intake.id)
                    const status = intake.status || 'pending'

                    return (
                      <tr key={intake.id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4 font-medium text-gray-900">
                          {intake.first_name}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {intake.version}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {Object.keys(intake.responses || {}).length}
                        </td>
                        <td className="px-6 py-4">
                          <StatusBadge status={isGenerating ? 'analyzing' : status} />
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {new Date(intake.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            {report?.status === 'complete' ? (
                              <button
                                onClick={() => handleDownload(intake.id, intake.first_name)}
                                className="text-sm px-3 py-1 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition font-medium"
                              >
                                Download
                              </button>
                            ) : (
                              <button
                                onClick={() => handleGenerate(intake.id)}
                                disabled={isGenerating}
                                className="text-sm px-3 py-1 bg-sa-50 text-sa-700 rounded-lg hover:bg-sa-100 transition font-medium disabled:opacity-50"
                              >
                                {isGenerating ? 'Generating...' : 'Generate'}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
