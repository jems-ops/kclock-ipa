import { useState, useEffect } from 'react'

export default function TestPage() {
  const [api, setApi] = useState('checking…')
  const [time] = useState(new Date().toLocaleTimeString())

  useEffect(() => {
    fetch('/api/health')
      .then(r => r.json())
      .then(d => setApi(`✅ ${JSON.stringify(d)}`))
      .catch(e => setApi(`❌ ${e.message}`))
  }, [])

  return (
    <div style={{ fontFamily: 'monospace', padding: 32, background: '#030712', color: '#f1f5f9', minHeight: '100vh' }}>
      <h1 style={{ color: '#6366f1', fontSize: 24, marginBottom: 24 }}>🧪 Diagnostic Page</h1>
      <table style={{ borderCollapse: 'collapse', width: '100%', maxWidth: 600 }}>
        {[
          ['React',       '✅ rendering'],
          ['CSS',         <span style={{ color: '#10b981' }}>✅ inline styles work</span>],
          ['Routing',     '✅ /test route active'],
          ['Time',        time],
          ['Backend API', api],
          ['User Agent',  navigator.userAgent.slice(0, 60) + '…'],
        ].map(([k, v]) => (
          <tr key={k} style={{ borderBottom: '1px solid #1e293b' }}>
            <td style={{ padding: '10px 16px', color: '#64748b', width: 160 }}>{k}</td>
            <td style={{ padding: '10px 16px' }}>{v}</td>
          </tr>
        ))}
      </table>
      <div style={{ marginTop: 32, display: 'flex', gap: 12 }}>
        <a href="/" style={{ color: '#6366f1' }}>← Landing</a>
        <a href="/dashboard" style={{ color: '#6366f1' }}>Dashboard</a>
        <a href="/docs" style={{ color: '#6366f1' }}>API Docs</a>
      </div>
    </div>
  )
}
