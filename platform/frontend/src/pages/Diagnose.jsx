import { useEffect, useState } from 'react'

import { Bot, Send, Loader, ChevronDown, ChevronUp } from 'lucide-react'
import { api } from '../api'

export default function Diagnose() {
  const [jobs, setJobs] = useState([])
  const [apps, setApps] = useState([])
  const [appId, setAppId] = useState('')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    api.getDiags().then(setJobs)
    api.getApps().then(setApps)
  }, [])

  const run = async () => {
    if (!appId || !question.trim()) return
    setLoading(true)
    try {
      const j = await api.diagnose({ app_id: appId, question })
      setJobs(p => [j, ...p])
      setExpanded(j.id)
      setQuestion('')
    } catch (e) { alert(e.message) }
    finally { setLoading(false) }
  }

  const onKey = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); run() } }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bot className="w-6 h-6 text-purple-400" /> AI Diagnose
        </h1>
        <p className="text-sm text-slate-500 mt-1">Ask the AI about any SAML/OIDC issue. Powered by local Ollama.</p>
      </div>

      {/* Input */}
      <div className="glass rounded-2xl p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-3 mb-3">
          <select value={appId} onChange={e => setAppId(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-purple-500 transition-colors sm:w-48">
            <option value="">Select app…</option>
            {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          <div className="flex flex-1 gap-2">
            <textarea value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={onKey}
              placeholder="Why is SAML failing? What's causing the login error?…"
              rows={1}
              className="flex-1 bg-slate-900 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-purple-500 transition-colors resize-none" />
            <button onClick={run} disabled={loading || !appId || !question.trim()}
              className="bg-purple-700 hover:bg-purple-600 disabled:opacity-40 text-white px-4 py-2.5 rounded-xl transition-all flex items-center gap-2 shrink-0">
              {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span className="hidden sm:inline text-sm font-medium">Diagnose</span>
            </button>
          </div>
        </div>
        <p className="text-xs text-slate-600">Press Enter to submit · Shift+Enter for new line</p>
      </div>

      {/* Results */}
      <div className="space-y-3">
        {jobs.map((j, i) => (
          <div key={j.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}
            className="glass rounded-xl overflow-hidden">
            <button onClick={() => setExpanded(expanded === j.id ? null : j.id)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-800/30 transition-colors text-left">
              <div className="flex items-center gap-3 min-w-0">
                <Bot className="w-4 h-4 text-purple-400 shrink-0" />
                <div className="min-w-0">
                  <span className="text-xs font-medium text-indigo-400 mr-2">{j.app_id}</span>
                  <span className="text-sm text-slate-300 truncate">{j.question}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0 ml-3">
                <span className="text-xs text-slate-600 hidden sm:block">{new Date(j.created_at).toLocaleString()}</span>
                {expanded === j.id ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </div>
            </button>
            
              {expanded === j.id && (
                <div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden border-t border-slate-800">
                  <div className="p-4 bg-slate-900/50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs text-slate-500 font-mono">{j.model_used}</span>
                    </div>
                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{j.diagnosis}</pre>
                  </div>
                </div>
              )}
            
          </div>
        ))}
        {jobs.length === 0 && (
          <div className="glass rounded-xl p-10 text-center text-slate-600">
            <Bot className="w-8 h-8 mx-auto mb-2 opacity-30" />No diagnoses yet. Ask the AI something.
          </div>
        )}
      </div>
    </div>
  )
}
