const BASE = '/api'

async function request(path, options = {}) {
  const { body, ...rest } = options
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...rest.headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...rest,
  })

  if (res.status === 204) return null

  const data = await res.json().catch(() => ({ detail: 'サーバーエラーが発生しました。' }))

  if (!res.ok) {
    throw new Error(data.detail || 'リクエストに失敗しました。')
  }
  return data
}

export const api = {
  auth: {
    me: ()               => request('/auth/me'),
    register: (body)     => request('/auth/register', { method: 'POST', body }),
    login: (body)        => request('/auth/login',    { method: 'POST', body }),
    logout: ()           => request('/auth/logout',   { method: 'POST' }),
  },
  polls: {
    list: ()             => request('/polls/'),
    create: (body)       => request('/polls/',         { method: 'POST', body }),
    get: (id)            => request(`/polls/${id}`),
    update: (id, body)   => request(`/polls/${id}`,   { method: 'PUT',  body }),
    delete: (id)         => request(`/polls/${id}`,   { method: 'DELETE' }),
    results: (id)        => request(`/polls/${id}/results`),
    csvUrl: (id)         => `${BASE}/polls/${id}/results/csv`,
  },
  vote: {
    getPoll: (pid)       => request(`/vote/${pid}`),
    getStatus: (pid)     => request(`/vote/${pid}/status`),
    submit: (pid, voteData) => request(`/vote/${pid}`, { method: 'POST', body: { vote_data: voteData } }),
  },
}
