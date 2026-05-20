import { useEffect, useState } from 'react'

import { FileText, RefreshCw } from 'lucide-react'
import { api } from '../api'

const ACTION_COLOR = {
  'app.create':      'text-indigo-400',
  'onboard.start':   'text-cyan-400',
  'diagnose':        'text-purple-400',
  'compliance.scan': 'text-green-400',
}

export default function Audit() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api.getAudit().then(d => { setLogs(d); setLoading(false) })
  }
  useEffect(load, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="w-6 h-6 text-slate-400" /> Audit Log
          </h1>
          <p className="text-sm text-slate-500 mt-1">Immutable record of every platform action.</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 text-sm border border-slate-700 hover:border-indigo-500 px-3 py-2 rounded-lg transition-colors text-slate-400 hover:text-white">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Mobile */}
      <div className="sm:hidden space-y-2">
        {logs.map((l, i) => (
          <div key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
            className="glass rounded-xl p-3 text-xs">
            <div className="flex justify-between mb-1">
              <span className={`font-mono font-semibold ${ACTION_COLOR[l.action] || 'text-slate-400'}`}>{l.action}</span>
              <span className="text-slate-600">{new Date(l.created_at).toLocaleTimeString()}</span>
            </div>
            <div className="text-slate-400">{l.actor} → {l.resource || l.app_id}</div>
          </div>
        ))}
      </div>

      {/* Desktop */}
      <div className="hidden sm:block glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase tracking-wider">
              {['Actor','Action','Resource','App','Date'].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.map((l, i) => (
              <tr key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }}
                className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                <td className="px-4 py-3 text-slate-300">{l.actor}</td>
                <td className={`px-4 py-3 font-mono text-xs font-semibold ${ACTION_COLOR[l.action] || 'text-slate-400'}`}>{l.action}</td>
                <td className="px-4 py-3 text-slate-400">{l.resource}</td>
                <td className="px-4 py-3 text-slate-500 text-xs">{l.app_id}</td>
                <td className="px-4 py-3 text-slate-600 text-xs">{new Date(l.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {!loading && logs.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-12 text-center text-slate-600">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />No audit entries yet.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
