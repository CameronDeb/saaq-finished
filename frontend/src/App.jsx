import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import IntakeForm from './pages/IntakeForm'
import ThankYou from './pages/ThankYou'
import Dashboard from './pages/Dashboard'
import MyDashboard from './pages/MyDashboard'
import PaymentSuccess from './pages/PaymentSuccess'

function ProtectedRoute({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-400">Loading...</div>
  if (!isAuthenticated) return <Navigate to="/login" />
  if (adminOnly && !isAdmin) return <Navigate to="/my" />
  return children
}

function AppRoutes() {
  const { isAuthenticated, isAdmin } = useAuth()

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to={isAdmin ? '/dashboard' : '/my'} /> : <Login />} />
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/" /> : <Signup />} />
      <Route path="/assessment/:version" element={<IntakeForm />} />
      <Route path="/thank-you" element={<ThankYou />} />
      <Route path="/payment-success" element={<PaymentSuccess />} />
      <Route path="/my" element={<ProtectedRoute><MyDashboard /></ProtectedRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute adminOnly><Dashboard /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
