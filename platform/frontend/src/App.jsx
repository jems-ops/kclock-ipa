import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Nav from './Nav'
import Landing from './pages/Landing'
import Apps from './pages/Apps'
import Onboarding from './pages/Onboarding'
import Diagnose from './pages/Diagnose'
import Compliance from './pages/Compliance'
import Audit from './pages/Audit'
import ApiDocs from './pages/ApiDocs'
import TestPage from './pages/TestPage'

function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#030712] text-slate-100">
      <Nav />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<Landing />} />
        <Route path="/test"       element={<TestPage />} />
        <Route path="/dashboard"  element={<DashboardLayout><Apps /></DashboardLayout>} />
        <Route path="/onboarding" element={<DashboardLayout><Onboarding /></DashboardLayout>} />
        <Route path="/diagnose"   element={<DashboardLayout><Diagnose /></DashboardLayout>} />
        <Route path="/compliance" element={<DashboardLayout><Compliance /></DashboardLayout>} />
        <Route path="/audit"      element={<DashboardLayout><Audit /></DashboardLayout>} />
        <Route path="/docs"       element={<DashboardLayout><ApiDocs /></DashboardLayout>} />
      </Routes>
    </BrowserRouter>
  )
}
