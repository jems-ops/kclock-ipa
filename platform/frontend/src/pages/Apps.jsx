import { useEffect, useState } from 'react'

import { Server, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { api } from '../api'

export default function Apps() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = () => {
    setLoading(true)
    api.getApps().then(d => { setApps(d); setLoading(false) }).catch(e => { setError(e.message); setLoading(false) })
  }
  useEffect(load, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Registered Apps</h1>
          <p className="text-sm text-slate-500 mt-1">All SAML/OIDC service providers managed by the platform.</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 text-sm border border-slate-700 hover:border-indigo-500 px-3 py-2 rounded-lg transition-colors text-slate-400 hover:text-white">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {error && <div className="glass border-red-900/50 rounded-xl p-4 text-red-400 text-sm mb-4">{error}</div>}

      {/* Mobile cards */}
      <div className="grid sm:hidden gap-3">
        {apps.map((a, i) => (
          <div key={a.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
            className="glass rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">{a.name}</span>
              {a.enabled ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
            </div>
            <div className="text-xs text-slate-500 font-mono">{a.id}</div>
            <a href={a.base_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-400 hover:underline">{a.base_url}</a>
          </div>
        ))}
        {!loading && apps.length === 0 && (
          <div className="glass rounded-xl p-8 text-center text-slate-500">
            <Server className="w-8 h-8 mx-auto mb-2 opacity-30" />
            No apps registered yet.
          </div>
        )}
      </div>

      {/* Desktop table */}
      <div className="hidden sm:block glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-wider">
              {['ID','Name','Base URL','Host Group','SAML Client','Status'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {apps.map((a, i) => (
              <tr key={a.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.04 }}
                className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{a.id}</td>
                <td className="px-4 py-3 font-medium text-white">{a.name}</td>
                <td className="px-4 py-3"><a href={a.base_url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline text-xs">{a.base_url}</a></td>
                <td className="px-4 py-3 text-slate-400">{a.host_group}</td>
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{a.saml_client_id}</td>
                <td className="px-4 py-3">
                  {a.enabled
                    ? <span className="flex items-center gap-1 text-green-400 text-xs"><CheckCircle className="w-3 h-3" /> Active</span>
                    : <span className="flex items-center gap-1 text-red-400 text-xs"><XCircle className="w-3 h-3" /> Disabled</span>}
                </td>
              </tr>
            ))}
            {!loading && apps.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-12 text-center text-slate-600">
                <Server className="w-8 h-8 mx-auto mb-2 opacity-30" />No apps registered yet.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
