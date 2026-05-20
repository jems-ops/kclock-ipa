import { useEffect, useState, useCallback, useRef } from 'react'
import { Play, RefreshCw, Clock, CheckCircle, XCircle, Loader, Rocket, Activity, ChevronDown, ChevronUp, Ban, Network, Users } from 'lucide-react'
import { api } from '../api'

const STATUS = {
  pending:   { color: 'bg-yellow-900/60 text-yellow-400', icon: Clock },
  running:   { color: 'bg-blue-900/60 text-blue-400',     icon: Loader },
  succeeded: { color: 'bg-green-900/60 text-green-400',   icon: CheckCircle },
  failed:    { color: 'bg-red-900/60 text-red-400',       icon: XCircle },
}

const FED_TYPES = [
  { value: 'full_federation', label: 'Full Federation',  desc: 'FreeIPA prep + Keycloak LDAP wiring (recommended)' },
  { value: 'freeipa_prep',    label: 'FreeIPA Prep Only', desc: 'Create bind accounts and export CA cert' },
  { value: 'ldap_only',       label: 'LDAP Wiring Only',  desc: 'Configure Keycloak LDAP provider (FreeIPA already prepped)' },
  { value: 'user_sync',       label: 'User Sync',         desc: 'Trigger LDAP user sync in Keycloak' },
]

function FederationTab() {
  const [jobs, setJobs]       = useState([])
  const [jobType, setJobType] = useState('full_federation')
  const [loading, setLoading] = useState(false)
  const [msg, setMsg]         = useState(null)
  const [cancelLoading, setCancelLoading] = useState({})
  const [expanded, setExpanded] = useState(null)
  const pollRef = useRef(null)

  const load = useCallback(() => api.getFedJobs().then(setJobs).catch(() => {}), [])
  useEffect(() => { load() }, [])

  useEffect(() => {
    const hasRunning = jobs.some(j => j.status === 'running' || j.status === 'pending')
    if (hasRunning && !pollRef.current) pollRef.current = setInterval(load, 4000)
    else if (!hasRunning && pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [jobs, load])

  const start = async () => {
    setLoading(true); setMsg(null)
    try {
      const j = await api.startFedJob({ job_type: jobType, triggered_by: 'manual' })
      setJobs(p => [j, ...p])
      setMsg({ type: 'ok', text: `Federation job started: ${FED_TYPES.find(t => t.value === jobType)?.label}` })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setLoading(false) }
  }

  const cancel = async (id) => {
    setCancelLoading(p => ({ ...p, [id]: true }))
    try {
      const j = await api.cancelFedJob(id)
      setJobs(p => p.map(x => x.id === j.id ? j : x))
      setMsg({ type: 'warn', text: 'Job cancelled.' })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setCancelLoading(p => ({ ...p, [id]: false })) }
  }

  return (
    <div>
      {/* Config card */}
      <div className="glass rounded-2xl p-5 mb-6">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-4">
          <Network className="w-4 h-4 text-cyan-400" /> FreeIPA → Keycloak LDAP Federation
        </h2>
        <div className="grid sm:grid-cols-2 gap-3 mb-4">
          {FED_TYPES.map(t => (
            <label key={t.value}
              className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                jobType === t.value ? 'border-cyan-500 bg-cyan-900/20' : 'border-slate-700 hover:border-slate-600'
              }`}>
              <input type="radio" name="fed_type" value={t.value} checked={jobType === t.value}
                onChange={() => setJobType(t.value)} className="mt-0.5 accent-cyan-500" />
              <div>
                <div className="text-sm font-medium text-white">{t.label}</div>
                <div className="text-xs text-slate-500 mt-0.5">{t.desc}</div>
              </div>
            </label>
          ))}
        </div>

        {/* Info panel */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mb-4 text-xs text-slate-400 space-y-1">
          <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-2">
            <Users className="w-3 h-3" /> What this does
          </div>
          {jobType === 'full_federation' && <>
            <p>1. Creates <code className="text-yellow-300">svc.ldap</code> + <code className="text-yellow-300">svc.keycloak</code> service accounts in FreeIPA</p>
            <p>2. Exports FreeIPA CA cert → imports into Keycloak JKS truststore</p>
            <p>3. Creates/updates LDAP UserStorageProvider in Keycloak realm <code className="text-yellow-300">master</code></p>
            <p>4. Configures user/group mappers and triggers full user sync</p>
          </>}
          {jobType === 'freeipa_prep' && <>
            <p>Creates bind service accounts in FreeIPA and exports the CA certificate.</p>
            <p>Run this first if Keycloak is not yet reachable.</p>
          </>}
          {jobType === 'ldap_only' && <>
            <p>Wires Keycloak LDAP provider against an already-prepped FreeIPA.</p>
            <p>Requires <code className="text-yellow-300">svc.ldap</code> to already exist in FreeIPA.</p>
          </>}
          {jobType === 'user_sync' && <>
            <p>Triggers a full LDAP user sync in Keycloak without changing any config.</p>
            <p>Use after adding new users in FreeIPA.</p>
          </>}
        </div>

        <button onClick={start} disabled={loading}
          className="flex items-center justify-center gap-2 bg-cyan-700 hover:bg-cyan-600 disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all w-full">
          {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Run Federation Job
        </button>
      </div>

      {msg && (
        <div className={`glass rounded-xl px-4 py-3 mb-4 text-sm ${
          msg.type === 'ok' ? 'text-green-400' : msg.type === 'warn' ? 'text-yellow-400' : 'text-red-400'}`}>
          {msg.text}
        </div>
      )}

      {/* Job history */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-400">Federation Job History</h3>
        <button onClick={load} className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>
      <div className="space-y-3">
        {jobs.map(j => {
          const s = STATUS[j.status] || STATUS.pending
          const Icon = s.icon
          const canCancel = j.status === 'pending' || j.status === 'running'
          return (
            <div key={j.id} className="glass rounded-xl overflow-hidden">
              <div className="p-4 flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-medium text-white">{FED_TYPES.find(t => t.value === j.job_type)?.label || j.job_type}</span>
                    <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${s.color}`}>
                      <Icon className={`w-3 h-3 ${j.status === 'running' ? 'animate-spin' : ''}`} />
                      {j.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 font-mono truncate">{j.id}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {canCancel && (
                    <button onClick={() => cancel(j.id)} disabled={cancelLoading[j.id]}
                      className="flex items-center gap-1.5 border border-red-800 hover:bg-red-900/40 text-red-400 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all">
                      {cancelLoading[j.id] ? <Loader className="w-3 h-3 animate-spin" /> : <Ban className="w-3 h-3" />}
                      Cancel
                    </button>
                  )}
                  {(j.log_output || j.error) && (
                    <button onClick={() => setExpanded(expanded === j.id ? null : j.id)}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
                      {expanded === j.id ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />} Logs
                    </button>
                  )}
                  <div className="text-right">
                    <p className="text-xs text-slate-500">{j.triggered_by}</p>
                    <p className="text-xs text-slate-600">{new Date(j.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>
              {expanded === j.id && (j.log_output || j.error) && (
                <div className="border-t border-slate-800 bg-slate-950/50 p-4">
                  {j.error && <p className="text-xs text-red-400 mb-2 font-semibold">{j.error}</p>}
                  {j.log_output && <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">{j.log_output}</pre>}
                </div>
              )}
            </div>
          )
        })}
        {jobs.length === 0 && (
          <div className="glass rounded-xl p-10 text-center text-slate-600">
            <Network className="w-8 h-8 mx-auto mb-2 opacity-30" />No federation jobs yet.
          </div>
        )}
      </div>
    </div>
  )
}

// Simulated task steps shown while a job is running
const TASK_STEPS = [
  'Connecting to host…',
  'Detecting installation directory…',
  'Fetching Keycloak OIDC metadata…',
  'Creating Keycloak client…',
  'Writing configuration…',
  'Restarting service…',
  'Validating SSO login…',
]

function TaskProgress({ job }) {
  const [step, setStep] = useState(0)
  useEffect(() => {
    if (job.status !== 'running') return
    const t = setInterval(() => setStep(s => Math.min(s + 1, TASK_STEPS.length - 1)), 4000)
    return () => clearInterval(t)
  }, [job.status])

  if (job.status === 'succeeded') {
    return (
      <div className="mt-3 space-y-1">
        {TASK_STEPS.map((t, i) => (
          <div key={i} className="flex items-center gap-2 text-xs text-green-400">
            <CheckCircle className="w-3 h-3 shrink-0" /> {t}
          </div>
        ))}
      </div>
    )
  }
  if (job.status === 'running') {
    return (
      <div className="mt-3 space-y-1">
        {TASK_STEPS.slice(0, step + 1).map((t, i) => (
          <div key={i} className={`flex items-center gap-2 text-xs ${i === step ? 'text-blue-400' : 'text-slate-500'}`}>
            {i === step
              ? <Loader className="w-3 h-3 shrink-0 animate-spin" />
              : <CheckCircle className="w-3 h-3 shrink-0 text-green-600" />}
            {t}
          </div>
        ))}
      </div>
    )
  }
  return null
}

export default function Onboarding() {
  const [jobs, setJobs] = useState([])
  const [apps, setApps] = useState([])
  const [appId, setAppId] = useState('')
  const [loading, setLoading] = useState(false)
  const [execLoading, setExecLoading] = useState({})
  const [cancelLoading, setCancelLoading] = useState({})
  const [monLoading, setMonLoading] = useState(false)
  const [msg, setMsg] = useState(null)
  const [expandedJob, setExpandedJob] = useState(null)
  const [activeTab, setActiveTab] = useState('sso')
  const pollRef = useRef(null)

  const refreshJobs = useCallback(() => api.getJobs().then(setJobs), [])

  useEffect(() => {
    refreshJobs()
    api.getApps().then(setApps)
  }, [])

  // Poll running jobs every 4s
  useEffect(() => {
    const hasRunning = jobs.some(j => j.status === 'running')
    if (hasRunning && !pollRef.current) {
      pollRef.current = setInterval(refreshJobs, 4000)
    } else if (!hasRunning && pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [jobs, refreshJobs])

  const start = async () => {
    if (!appId) return
    setLoading(true); setMsg(null)
    try {
      const j = await api.startJob({ app_id: appId, triggered_by: 'manual' })
      setJobs(p => [j, ...p])
      setMsg({ type: 'ok', text: `Job created for ${appId} — click Execute to run the playbook.` })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setLoading(false) }
  }

  const execute = async (jobId, appId) => {
    setExecLoading(p => ({ ...p, [jobId]: true }))
    setMsg(null)
    try {
      const j = await api.executeJob(jobId)
      setJobs(p => p.map(x => x.id === j.id ? j : x))
      setMsg({ type: 'ok', text: `Playbook started for ${j.app_id}. Polling for status…` })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setExecLoading(p => ({ ...p, [jobId]: false })) }
  }

  const cancel = async (jobId) => {
    setCancelLoading(p => ({ ...p, [jobId]: true }))
    setMsg(null)
    try {
      const j = await api.cancelJob(jobId)
      setJobs(p => p.map(x => x.id === j.id ? j : x))
      setMsg({ type: 'warn', text: `Job for ${j.app_id} cancelled.` })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setCancelLoading(p => ({ ...p, [jobId]: false })) }
  }

  const deployMonitoring = async () => {
    setMonLoading(true); setMsg(null)
    try {
      const j = await api.deployMonitoringAgents()
      setJobs(p => [j, ...p])
      setMsg({ type: 'ok', text: 'Monitoring agents deployment started.' })
    } catch (e) { setMsg({ type: 'err', text: e.message }) }
    finally { setMonLoading(false) }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Onboarding</h1>
        <p className="text-sm text-slate-500 mt-1">Trigger and track SAML/OIDC onboarding runs and infrastructure deployments.</p>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 mb-6 border-b border-slate-800">
        {[
          { id: 'sso',        label: 'SSO Onboarding',    icon: Rocket  },
          { id: 'federation', label: 'LDAP Federation',   icon: Network },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === t.id
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {activeTab === 'federation' ? <FederationTab /> : (<div>
      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div className="glass rounded-2xl p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-3">
            <Rocket className="w-4 h-4 text-indigo-400" /> SSO Onboarding
          </h2>
          <div className="flex flex-col gap-3">
            <select value={appId} onChange={e => setAppId(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-indigo-500 transition-colors">
              <option value="">Select application…</option>
              {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <button onClick={start} disabled={loading || !appId}
              className="flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all">
              {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Create Onboarding Job
            </button>
          </div>
        </div>

        <div className="glass rounded-2xl p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-300 mb-3">
            <Activity className="w-4 h-4 text-cyan-400" /> Monitoring Agents
          </h2>
          <p className="text-xs text-slate-500 mb-3">Deploy node_exporter to all application servers and register Prometheus scrape targets.</p>
          <button onClick={deployMonitoring} disabled={monLoading}
            className="flex items-center justify-center gap-2 bg-cyan-700 hover:bg-cyan-600 disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all w-full">
            {monLoading ? <Loader className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
            Deploy Monitoring Agents
          </button>
        </div>
      </div>

      {msg && (
        <div className={`glass rounded-xl px-4 py-3 mb-4 text-sm ${
          msg.type === 'ok'   ? 'text-green-400 border-green-900/50' :
          msg.type === 'warn' ? 'text-yellow-400 border-yellow-900/50' :
                                'text-red-400 border-red-900/50'}`}>
          {msg.text}
        </div>
      )}

      {/* Jobs list */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-400">Job History</h2>
        <button onClick={refreshJobs} className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      <div className="space-y-3">
        {jobs.map(j => {
          const s = STATUS[j.status] || STATUS.pending
          const Icon = s.icon
          const isExpanded = expandedJob === j.id
          const canCancel = j.status === 'pending' || j.status === 'running'
          return (
            <div key={j.id} className="glass rounded-xl overflow-hidden">
              <div className="p-4 flex flex-col sm:flex-row sm:items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-medium text-white">{j.app_id}</span>
                    <span className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${s.color}`}>
                      <Icon className={`w-3 h-3 ${j.status === 'running' ? 'animate-spin' : ''}`} />
                      {j.status}
                    </span>
                    {j.playbook && <span className="text-xs text-slate-600 font-mono">{j.playbook}</span>}
                  </div>
                  <p className="text-xs text-slate-500 font-mono truncate mb-1">{j.id}</p>
                  {/* Task step progress */}
                  {(j.status === 'running' || j.status === 'succeeded') && <TaskProgress job={j} />}
                </div>

                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                  {j.status === 'pending' && (
                    <button onClick={() => execute(j.id, j.app_id)} disabled={execLoading[j.id]}
                      className="flex items-center gap-1.5 bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition-all">
                      {execLoading[j.id] ? <Loader className="w-3 h-3 animate-spin" /> : <Rocket className="w-3 h-3" />}
                      Execute
                    </button>
                  )}
                  {canCancel && (
                    <button onClick={() => cancel(j.id)} disabled={cancelLoading[j.id]}
                      className="flex items-center gap-1.5 border border-red-800 hover:bg-red-900/40 disabled:opacity-40 text-red-400 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all">
                      {cancelLoading[j.id] ? <Loader className="w-3 h-3 animate-spin" /> : <Ban className="w-3 h-3" />}
                      Cancel
                    </button>
                  )}
                  {(j.log_output || j.error) && (
                    <button onClick={() => setExpandedJob(isExpanded ? null : j.id)}
                      className="flex items-center gap-1 text-xs text-slate-500 hover:text-white transition-colors">
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      Logs
                    </button>
                  )}
                  <div className="text-right">
                    <p className="text-xs text-slate-500">{j.triggered_by}</p>
                    <p className="text-xs text-slate-600">{new Date(j.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {isExpanded && (j.log_output || j.error) && (
                <div className="border-t border-slate-800 bg-slate-950/50 p-4">
                  {j.error && <p className="text-xs text-red-400 mb-2 font-semibold">{j.error}</p>}
                  {j.log_output && (
                    <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">{j.log_output}</pre>
                  )}
                </div>
              )}
            </div>
          )
        })}
        {jobs.length === 0 && (
          <div className="glass rounded-xl p-10 text-center text-slate-600">
            <RefreshCw className="w-8 h-8 mx-auto mb-2 opacity-30" />No jobs yet.
          </div>
        )}
      </div>
    </div>)}
    </div>
  )
}

