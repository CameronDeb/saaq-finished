import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import Logo from '../components/Logo'

export default function Dashboard() {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState('reports')
  const [stats, setStats] = useState(null)
  const [intakes, setIntakes] = useState([])
  const [reports, setReports] = useState([])
  const [users, setUsers] = useState([])
  const [payments, setPayments] = useState([])
  const [prices, setPrices] = useState({})
  const [healthData, setHealthData] = useState(null)
  const [grantEmail, setGrantEmail] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    try {
      const [s, i, r, h] = await Promise.all([
        api.adminDashboard().catch(() => null),
        api.listIntakes().catch(() => ({ intakes: [] })),
        api.listReports().catch(() => ({ reports: [] })),
        api.health().catch(() => null),
      ])
      setStats(s)
      setIntakes(i.intakes || [])
      setReports(r.reports || [])
      setHealthData(h)
    } catch {}
    setLoading(false)
  }

  const loadUsers = async () => {
    try {
      const res = await api.adminUsers()
      setUsers(res.users || [])
    } catch {}
  }

  const loadPayments = async () => {
    try {
      const res = await api.adminPayments()
      setPayments(res.payments || [])
    } catch {}
  }

  const loadPrices = async () => {
    try {
      const res = await api.adminSettings()
      const p = {}
      for (const s of (res.settings || [])) {
        if (s.key.startsWith('price_')) p[s.key] = s.value
      }
      setPrices(p)
    } catch {}
  }

  useEffect(() => {
    if (tab === 'users') loadUsers()
    if (tab === 'payments') loadPayments()
    if (tab === 'pricing') loadPrices()
  }, [tab])

  const handleGenerate = async (intakeId) => {
    try {
      await api.generateReport(intakeId)
      setTimeout(loadAll, 2000)
    } catch (err) { alert(err.message) }
  }

  const handleDownload = async (intakeId, name) => {
    try {
      const blob = await api.downloadReport(intakeId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url; a.download = `SAAQReport-${name}.docx`; a.click()
      URL.revokeObjectURL(url)
    } catch (err) { alert(err.message) }
  }

  const handlePriceUpdate = async (key, amount, label) => {
    try {
      await api.updatePrice(key, amount, label)
      loadPrices()
    } catch (err) { alert(err.message) }
  }

  const handleGrantAdmin = async () => {
    if (!grantEmail) return
    try {
      await api.grantAdmin(grantEmail)
      setGrantEmail('')
      loadUsers()
    } catch (err) { alert(err.message) }
  }

  const handleRevokeAdmin = async (email) => {
    if (!confirm(`Revoke admin from ${email}?`)) return
    try {
      await api.revokeAdmin(email)
      loadUsers()
    } catch (err) { alert(err.message) }
  }

  const getReportStatus = (intakeId) => {
    const r = reports.find(rep => rep.intake_id === intakeId)
    return r?.status || 'pending'
  }

  const tabs = [
    { id: 'reports', label: 'Reports' },
    { id: 'users', label: 'Users' },
    { id: 'payments', label: 'Payments' },
    { id: 'pricing', label: 'Pricing' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/"><Logo size={36} /></Link>
            <span className="text-lg font-semibold text-gray-800">Admin Dashboard</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm text-gray-500 hover:text-gray-700">Back to site</Link>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-gray-600">Sign out</button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* stats cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Total Submissions', val: stats.total_submissions, color: 'blue' },
              { label: 'Reports Complete', val: stats.reports_complete, color: 'green' },
              { label: 'Revenue', val: `$${stats.total_revenue?.toLocaleString() || 0}`, color: 'emerald' },
              { label: 'Total Users', val: stats.total_users, color: 'purple' },
            ].map(s => (
              <div key={s.label} className="bg-white rounded-xl border p-4">
                <p className="text-xs text-gray-400 uppercase">{s.label}</p>
                <p className={`text-2xl font-bold text-${s.color}-600`}>{s.val}</p>
              </div>
            ))}
          </div>
        )}

        {/* health indicators */}
        {healthData && (
          <div className="flex gap-3 mb-6 text-xs">
            <span className={`px-2 py-1 rounded-full ${healthData.api_key_configured ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              API Key {healthData.api_key_configured ? 'Active' : 'Missing'}
            </span>
            <span className={`px-2 py-1 rounded-full ${healthData.pipeline_available ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
              DOCX Pipeline {healthData.pipeline_available ? 'Ready' : 'Missing'}
            </span>
            <span className={`px-2 py-1 rounded-full ${healthData.database_configured ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
              {healthData.database_configured ? 'Supabase' : 'In-Memory DB'}
            </span>
            <span className={`px-2 py-1 rounded-full ${healthData.stripe_configured ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
              Stripe {healthData.stripe_configured ? 'Active' : 'Not Set'}
            </span>
          </div>
        )}

        {/* tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition ${tab === t.id ? 'bg-white shadow text-gray-800' : 'text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* ─── Reports tab ─── */}
        {tab === 'reports' && (
          <div className="bg-white rounded-xl border">
            <div className="p-4 border-b flex justify-between items-center">
              <h2 className="font-semibold text-gray-800">Submissions</h2>
              <button onClick={loadAll} className="text-sm text-blue-600 hover:underline">Refresh</button>
            </div>
            {intakes.length === 0 ? (
              <p className="p-6 text-gray-400 text-center">No submissions yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Version</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Responses</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Date</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
                  </tr></thead>
                  <tbody>
                    {intakes.map(intake => {
                      const status = getReportStatus(intake.id)
                      return (
                        <tr key={intake.id} className="border-b hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium">{intake.first_name}</td>
                          <td className="px-4 py-3">{intake.version}</td>
                          <td className="px-4 py-3">{Object.keys(intake.responses || {}).length}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                              status === 'complete' ? 'bg-green-100 text-green-700' :
                              status === 'failed' ? 'bg-red-100 text-red-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>{status}</span>
                          </td>
                          <td className="px-4 py-3 text-gray-400">{new Date(intake.submitted_at || intake.created_at).toLocaleDateString()}</td>
                          <td className="px-4 py-3">
                            {status === 'complete' ? (
                              <button onClick={() => handleDownload(intake.id, intake.first_name)} className="text-blue-600 hover:underline text-sm">Download</button>
                            ) : status === 'failed' || status === 'pending' ? (
                              <button onClick={() => handleGenerate(intake.id)} className="text-blue-600 hover:underline text-sm">Generate</button>
                            ) : (
                              <span className="text-gray-400 text-sm">Processing...</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ─── Users tab ─── */}
        {tab === 'users' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Grant admin access</h3>
              <div className="flex gap-2">
                <input value={grantEmail} onChange={e => setGrantEmail(e.target.value)}
                  placeholder="user@example.com" className="flex-1 border rounded-lg px-3 py-2 text-sm" />
                <button onClick={handleGrantAdmin} className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">Grant</button>
              </div>
            </div>
            <div className="bg-white rounded-xl border">
              <div className="p-4 border-b"><h2 className="font-semibold text-gray-800">All Users ({users.length})</h2></div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Email</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Role</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Total Spent</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Joined</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Actions</th>
                  </tr></thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium">{u.full_name || '-'}</td>
                        <td className="px-4 py-3">{u.email}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                            {u.role}
                          </span>
                        </td>
                        <td className="px-4 py-3">${u.total_spent || 0}</td>
                        <td className="px-4 py-3 text-gray-400">{new Date(u.created_at).toLocaleDateString()}</td>
                        <td className="px-4 py-3">
                          {u.role === 'admin' && u.email !== user?.email ? (
                            <button onClick={() => handleRevokeAdmin(u.email)} className="text-red-500 hover:underline text-sm">Revoke admin</button>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ─── Payments tab ─── */}
        {tab === 'payments' && (
          <div className="bg-white rounded-xl border">
            <div className="p-4 border-b"><h2 className="font-semibold text-gray-800">Payment History ({payments.length})</h2></div>
            {payments.length === 0 ? (
              <p className="p-6 text-gray-400 text-center">No payments yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b bg-gray-50">
                    <th className="text-left px-4 py-3 font-medium text-gray-500">User</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Product</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Amount</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                    <th className="text-left px-4 py-3 font-medium text-gray-500">Date</th>
                  </tr></thead>
                  <tbody>
                    {payments.map(p => (
                      <tr key={p.id} className="border-b hover:bg-gray-50">
                        <td className="px-4 py-3">{p.user_id?.slice(0, 8) || '-'}</td>
                        <td className="px-4 py-3">{p.product_type}</td>
                        <td className="px-4 py-3 font-medium">${p.amount}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            p.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                          }`}>{p.status}</span>
                        </td>
                        <td className="px-4 py-3 text-gray-400">{new Date(p.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ─── Pricing tab ─── */}
        {tab === 'pricing' && (
          <div className="bg-white rounded-xl border p-6">
            <h2 className="font-semibold text-gray-800 mb-4">Manage Pricing</h2>
            <p className="text-sm text-gray-500 mb-6">Update prices here. Changes take effect immediately for new checkouts.</p>
            <div className="space-y-4">
              {[
                { key: 'price_15q_report', defaultLabel: '15-Question Report Only' },
                { key: 'price_15q_bundle', defaultLabel: '15-Question Report + Sessions' },
                { key: 'price_30q_report', defaultLabel: '30-Question Report Only' },
                { key: 'price_30q_bundle', defaultLabel: '30-Question Report + Sessions' },
              ].map(item => {
                const current = prices[item.key] || { amount: 0, label: item.defaultLabel }
                return (
                  <PriceEditor key={item.key} priceKey={item.key} current={current} onSave={handlePriceUpdate} />
                )
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function PriceEditor({ priceKey, current, onSave }) {
  const [amount, setAmount] = useState(current.amount)
  const [label, setLabel] = useState(current.label)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    await onSave(priceKey, Number(amount), label)
    setSaving(false)
  }

  return (
    <div className="flex items-center gap-4 p-4 border rounded-lg">
      <div className="flex-1">
        <input value={label} onChange={e => setLabel(e.target.value)}
          className="w-full border rounded px-3 py-1.5 text-sm mb-1" />
        <p className="text-xs text-gray-400">{priceKey}</p>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-gray-500">$</span>
        <input type="number" value={amount} onChange={e => setAmount(e.target.value)}
          className="w-24 border rounded px-3 py-1.5 text-sm" />
      </div>
      <button onClick={handleSave} disabled={saving}
        className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
        {saving ? '...' : 'Save'}
      </button>
    </div>
  )
}
