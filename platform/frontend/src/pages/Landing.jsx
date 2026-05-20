import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Zap, GitBranch, Bot, ChevronRight, CheckCircle, AlertTriangle, Server, Lock, Activity, Network } from 'lucide-react'

const STATS = [
  { label: 'Apps Integrated', value: 12,    icon: Server,        color: 'text-indigo-400' },
  { label: 'SSO Enabled',     value: 9,     icon: Lock,          color: 'text-cyan-400'   },
  { label: 'Compliance',      value: '91%', icon: Shield,        color: 'text-green-400'  },
  { label: 'Drift Alerts',    value: 3,     icon: AlertTriangle, color: 'text-yellow-400' },
]

const FEATURES = [
  { icon: Lock,      title: 'Zero Trust SSO',     desc: 'Automate SAML/OIDC onboarding for every DevOps tool via Keycloak + FreeIPA.' },
  { icon: Bot,       title: 'AI Troubleshooting', desc: 'Local LLM diagnoses SAML failures, explains root causes, generates fixes.' },
  { icon: Shield,    title: 'STIG Compliance',    desc: 'Continuous drift detection with AI-generated remediation playbooks.' },
  { icon: GitBranch, title: 'Ansible Automation', desc: 'Idempotent roles for every integration. One command to onboard any app.' },
  { icon: Activity,  title: 'Audit Evidence',     desc: 'Immutable audit log of every action. Export compliance evidence instantly.' },
  { icon: Network,   title: 'LDAP Federation',    desc: 'FreeIPA ↔ Keycloak federation with group sync and role mapping.' },
]

const INTEGRATIONS = [
  { name: 'Jenkins',    on: true  }, { name: 'SonarQube',  on: true  },
  { name: 'Wazuh',      on: false }, { name: 'Jira',       on: true  },
  { name: 'Confluence', on: true  }, { name: 'Artifactory',on: true  },
  { name: 'Nessus',     on: false }, { name: 'Bitbucket',  on: true  },
  { name: 'Grafana',    on: false }, { name: 'Prometheus',  on: false },
]

const COMPLIANCE = [
  { name: 'PostgreSQL STIG', score: 92 },
  { name: 'FreeIPA STIG',    score: 89 },
  { name: 'Apache STIG',     score: 95 },
  { name: 'DNS STIG',        score: 87 },
]

const AI_TABS = {
  diagnose: {
    prompt: 'Why is Wazuh SAML failing?',
    items: [
      { label: 'Root Cause', color: 'text-yellow-400', text: "ACS URL mismatch — Keycloak redirect URI doesn't match Wazuh's endpoint." },
      { label: 'Fix',        color: 'text-green-400',  text: 'Update wazuh_base_url in group_vars/all/main.yml and re-run sso-cli onboard-app wazuh.' },
      { label: 'Verify',     color: 'text-cyan-400',   text: 'Check Keycloak admin events for LOGIN_ERROR after next login attempt.' },
    ]
  },
  onboard: {
    prompt: 'Onboard Grafana with OIDC',
    items: [
      { label: 'Note',   color: 'text-yellow-400', text: 'Grafana OSS uses generic_oauth — SAML requires Enterprise.' },
      { label: 'Fix',    color: 'text-green-400',  text: 'Run: sso-cli ai-onboard grafana --service grafana-server' },
      { label: 'Verify', color: 'text-cyan-400',   text: 'Open grafana.local → Sign in with Keycloak → FreeIPA credentials.' },
    ]
  },
  compliance: {
    prompt: 'Summarize RHEL9 STIG findings',
    items: [
      { label: 'Findings', color: 'text-yellow-400', text: '3 high-severity: V-205157 password complexity, V-205224 audit config, V-206562 SSH hardening.' },
      { label: 'Fix',      color: 'text-green-400',  text: 'Run: ansible-playbook stig-remediate.yml --tags high' },
      { label: 'Verify',   color: 'text-cyan-400',   text: 'Re-scan with OpenSCAP. Expected improvement: 87% → 96%.' },
    ]
  },
}

function Counter({ target }) {
  const [val, setVal] = useState(0)
  const isNum = typeof target === 'number'
  useEffect(() => {
    if (!isNum) return
    let n = 0
    const step = Math.ceil(target / 40)
    const t = setInterval(() => {
      n = Math.min(n + step, target)
      setVal(n)
      if (n >= target) clearInterval(t)
    }, 30)
    return () => clearInterval(t)
  }, [target, isNum])
  return <>{isNum ? val : target}</>
}

function Bar({ score }) {
  const color = score >= 90 ? 'bg-green-500' : 'bg-yellow-500'
  return (
    <div className="w-full bg-slate-800 rounded-full h-1.5">
      <div className={`h-1.5 rounded-full ${color} transition-all duration-1000`} style={{ width: `${score}%` }} />
    </div>
  )
}

export default function Landing() {
  const [tab, setTab] = useState('diagnose')

  return (
    <div className="bg-[#030712] text-slate-100 min-h-screen">

      {/* Hero */}
      <section className="grid-bg relative min-h-screen flex flex-col items-center justify-center px-4 py-24 text-center overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-4xl mx-auto fade-up">
          <span className="inline-flex items-center gap-2 text-xs font-semibold tracking-widest text-indigo-400 uppercase border border-indigo-800/60 bg-indigo-950/40 px-4 py-1.5 rounded-full mb-6">
            <Zap className="w-3 h-3" /> Zero Trust · FedRAMP-Ready · AI-Powered
          </span>
          <h1 className="text-4xl sm:text-5xl md:text-7xl font-extrabold leading-tight mb-6 tracking-tight">
            Identity &amp; Compliance<br />
            <span className="gradient-text">Automation Platform</span>
          </h1>
          <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Automate SSO onboarding, LDAP federation, STIG compliance, and AI-powered
            troubleshooting across enterprise and federal DevSecOps environments.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link to="/onboarding" className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-indigo-500/30">
              Start Onboarding <ChevronRight className="w-4 h-4" />
            </Link>
            <Link to="/diagnose" className="flex items-center gap-2 bg-purple-700 hover:bg-purple-600 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:-translate-y-0.5">
              <Bot className="w-4 h-4" /> AI Assistant
            </Link>
            <Link to="/compliance" className="flex items-center gap-2 border border-slate-700 hover:border-indigo-500 text-slate-300 hover:text-white px-6 py-3 rounded-xl font-semibold transition-all hover:-translate-y-0.5">
              <Shield className="w-4 h-4" /> Compliance Scan
            </Link>
          </div>
          <div className="mt-14 flex flex-wrap justify-center items-center gap-2 text-sm">
            {['Keycloak','↔','FreeIPA','↔','Apps','↔','Compliance','↔','AI Engine'].map((n, i) => (
              <span key={i} className={n === '↔' ? 'text-indigo-600 font-bold text-lg' : 'glass px-3 py-1 rounded-full text-indigo-300 text-xs font-medium'}>
                {n}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-4 border-y border-slate-800/60">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4">
          {STATS.map(s => (
            <div key={s.label} className="glass rounded-2xl p-6 text-center hover:glow transition-all duration-300 group">
              <s.icon className={`w-6 h-6 ${s.color} mx-auto mb-3 group-hover:scale-110 transition-transform`} />
              <div className={`text-3xl font-bold ${s.color} mb-1`}><Counter target={s.value} /></div>
              <div className="text-xs text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Everything you need</h2>
            <p className="text-slate-400 max-w-xl mx-auto">One platform for identity, compliance, and AI-assisted operations.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(f => (
              <div key={f.title} className="glass rounded-2xl p-6 hover:border-indigo-500/40 hover:glow-sm transition-all duration-300 group">
                <div className="w-10 h-10 rounded-xl bg-indigo-600/20 flex items-center justify-center mb-4 group-hover:bg-indigo-600/30 transition-colors">
                  <f.icon className="w-5 h-5 text-indigo-400" />
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Demo */}
      <section className="py-24 px-4 bg-slate-900/40 border-y border-slate-800/60">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">AI Security Assistant</h2>
            <p className="text-slate-400">Natural-language ops. No data leaves your environment.</p>
          </div>
          <div className="glass rounded-2xl overflow-hidden glow">
            <div className="bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <span className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="ml-3 text-xs text-slate-500 font-mono">AI Security Assistant — gemma3:270m · local</span>
            </div>
            <div className="flex border-b border-slate-800 bg-slate-900/50">
              {Object.keys(AI_TABS).map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-2.5 text-xs font-medium capitalize transition-colors ${tab === t ? 'text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300'}`}>
                  {t}
                </button>
              ))}
            </div>
            <div className="p-6 space-y-4 font-mono text-sm">
              <div className="flex gap-3">
                <span className="text-indigo-400 shrink-0">user@platform:~$</span>
                <span className="text-slate-200">{AI_TABS[tab].prompt}</span>
              </div>
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 space-y-3">
                {AI_TABS[tab].items.map((r, i) => (
                  <div key={i} className="flex gap-3 text-xs sm:text-sm">
                    <span className={`shrink-0 font-semibold ${r.color} w-20`}>{r.label}:</span>
                    <span className="text-slate-300">{r.text}</span>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                <Link to="/diagnose" className="bg-indigo-700 hover:bg-indigo-600 px-4 py-2 rounded-lg text-xs font-semibold transition-colors">Generate Fix</Link>
                <button className="border border-slate-700 hover:border-indigo-500 px-4 py-2 rounded-lg text-xs font-semibold transition-colors">Run Validation</button>
                <button className="border border-slate-700 hover:border-indigo-500 px-4 py-2 rounded-lg text-xs font-semibold transition-colors">Export Report</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Integrations</h2>
            <p className="text-slate-400">One-click SSO onboarding for your entire DevOps toolchain.</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {INTEGRATIONS.map(app => (
              <div key={app.name} className="glass rounded-xl p-4 flex flex-col items-center gap-2 hover:border-indigo-500/50 hover:glow-sm transition-all duration-300">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${app.on ? 'bg-indigo-600/30 text-indigo-300' : 'bg-slate-800 text-slate-500'}`}>
                  {app.name[0]}
                </div>
                <span className="text-xs font-medium text-center">{app.name}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${app.on ? 'bg-green-900/60 text-green-400' : 'bg-slate-800 text-slate-500'}`}>
                  {app.on ? 'SSO ON' : 'Disabled'}
                </span>
                <Link to="/onboarding" className={`text-xs transition-colors ${app.on ? 'text-slate-600 hover:text-slate-400' : 'text-indigo-400 hover:text-indigo-300'}`}>
                  {app.on ? 'Manage' : 'Enable →'}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="py-24 px-4 bg-slate-900/40 border-y border-slate-800/60">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">Compliance Engine</h2>
            <p className="text-slate-400">Continuous STIG/SRG drift detection with AI-generated remediation.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {COMPLIANCE.map(c => (
                <div key={c.name} className="glass rounded-xl p-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-300">{c.name}</span>
                    <span className={c.score >= 90 ? 'text-green-400 font-semibold' : 'text-yellow-400 font-semibold'}>{c.score}%</span>
                  </div>
                  <Bar score={c.score} />
                </div>
              ))}
            </div>
            <div className="glass rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Bot className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-semibold text-purple-400">AI Compliance Summary</h3>
              </div>
              <p className="text-sm text-slate-300 mb-4">3 high severity findings detected. Remediation playbooks available.</p>
              <div className="space-y-2 font-mono text-xs">
                {[
                  { id: 'V-205157', s: 'OPEN', c: 'text-red-400',   d: 'Password complexity not enforced' },
                  { id: 'V-205224', s: 'N/A',  c: 'text-slate-500', d: 'Not applicable to this host' },
                  { id: 'V-206562', s: 'PASS', c: 'text-green-400', d: 'Audit logging enabled' },
                ].map(f => (
                  <div key={f.id} className="flex gap-3 py-1.5 border-b border-slate-800 last:border-0">
                    <span className={`w-10 shrink-0 font-semibold ${f.c}`}>{f.s}</span>
                    <span className="text-slate-500">{f.id}</span>
                    <span className="text-slate-400 truncate">{f.d}</span>
                  </div>
                ))}
              </div>
              <Link to="/compliance" className="mt-4 inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300 transition-colors">
                Full Report <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-28 px-4 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Ready to automate your identity stack?</h2>
          <p className="text-slate-400 mb-8">From FreeIPA to Keycloak to every DevOps tool — one platform, one command.</p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/onboarding" className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-3 rounded-xl font-semibold transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-indigo-500/30">
              Get Started
            </Link>
            <Link to="/docs" className="border border-slate-700 hover:border-indigo-500 text-slate-300 hover:text-white px-8 py-3 rounded-xl font-semibold transition-all hover:-translate-y-0.5">
              API Docs
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 px-4 py-8 text-center text-xs text-slate-600">
        IPA Platform · Keycloak + FreeIPA + AI · Built for GovTech &amp; Enterprise DevSecOps
      </footer>
    </div>
  )
}
