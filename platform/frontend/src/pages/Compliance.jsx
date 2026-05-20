import { useEffect, useState } from 'react'

import { Shield, CheckCircle, XCircle, HelpCircle } from 'lucide-react'
import { api } from '../api'

const STATUS = {
  compliant:     { color: 'bg-green-900/60 text-green-400',  icon: CheckCircle },
  non_compliant: { color: 'bg-red-900/60 text-red-400',      icon: XCircle     },
  unknown:       { color: 'bg-slate-800 text-slate-400',     icon: HelpCircle  },
}

export default function Compliance() {
  const [reports, setReports] = useState([])
  useEffect(() => { api.getReports().then(setReports) }, [])

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield className="w-6 h-6 text-green-400" /> Compliance Reports
        </h1>
        <p className="text-sm text-slate-500 mt-1">STIG/SRG scan results per application.</p>
      </div>

      <div className="space-y-3">
        {reports.map((r, i) => {
          const s = STATUS[r.status] || STATUS.unknown
          const Icon = s.icon
          const pct = r.total_controls > 0 ? Math.round((r.passed / r.total_controls) * 100) : 0
          return (
            <div key={r.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
              className="glass rounded-xl p-4">
              <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-white">{r.app_id}</span>
                    <span className="text-xs text-slate-500">{r.stig_profile}</span>
                    <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${s.color}`}>
                      <Icon className="w-3 h-3" />{r.status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2">
                    <div className={`h-full rounded-full ${pct >= 90 ? 'bg-green-500' : pct >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8, ease: 'easeOut' }} />
                  </div>
                </div>
                <div className="flex gap-4 text-center shrink-0">
                  {[['Pass', r.passed, 'text-green-400'], ['Fail', r.failed, 'text-red-400'], ['N/A', r.not_applicable, 'text-slate-500']].map(([l, v, c]) => (
                    <div key={l}>
                      <div className={`text-lg font-bold ${c}`}>{v}</div>
                      <div className="text-xs text-slate-600">{l}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
        {reports.length === 0 && (
          <div className="glass rounded-xl p-10 text-center text-slate-600">
            <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />No compliance reports yet.
          </div>
        )}
      </div>
    </div>
  )
}
