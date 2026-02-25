import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import IntakeForm from './pages/IntakeForm'
import ThankYou from './pages/ThankYou'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/assessment" element={<IntakeForm />} />
        <Route path="/assessment/:version" element={<IntakeForm />} />
        <Route path="/thank-you" element={<ThankYou />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  )
}
