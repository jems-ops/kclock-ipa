const BASE = '/api'

async function req(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.status === 204 ? null : res.json()
}

export const api = {
  // Apps
  getApps:    ()           => req('GET',    '/apps'),
  createApp:  (data)       => req('POST',   '/apps', data),
  deleteApp:  (id)         => req('DELETE', `/apps/${id}`),

  // Onboarding
  getJobs:    (appId)      => req('GET',    `/onboarding${appId ? `?app_id=${appId}` : ''}`),
  getJob:     (id)         => req('GET',    `/onboarding/${id}`),
  startJob:   (data)       => req('POST',   '/onboarding', data),
  executeJob: (id)         => req('POST',   `/onboarding/${id}/execute`),
  cancelJob:  (id)         => req('POST',   `/onboarding/${id}/cancel`),
  deployMonitoringAgents: () => req('POST', '/onboarding/monitoring-agents'),

  // Diagnose
  getDiags:   (appId)      => req('GET',    `/diagnose${appId ? `?app_id=${appId}` : ''}`),
  diagnose:   (data)       => req('POST',   '/diagnose', data),

  // Compliance
  getReports: (appId)      => req('GET',    `/compliance${appId ? `?app_id=${appId}` : ''}`),

  // Audit
  getAudit:   (appId)      => req('GET',    `/audit${appId ? `?app_id=${appId}` : ''}`),

  // Federation
  getFedJobs:    ()         => req('GET',  '/federation'),
  startFedJob:   (data)     => req('POST', '/federation', data),
  cancelFedJob:  (id)       => req('POST', `/federation/${id}/cancel`),
  getFedJob:     (id)       => req('GET',  `/federation/${id}`),
}
