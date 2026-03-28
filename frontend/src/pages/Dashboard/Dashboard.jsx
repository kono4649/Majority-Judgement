import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import './Dashboard.css'

function pollStatus(poll) {
  const now = new Date()
  if (poll.start_time && new Date(poll.start_time) > now) return { label: '未開始', cls: 'warning' }
  if (poll.end_time   && new Date(poll.end_time)   < now) return { label: '終了',   cls: 'secondary' }
  return { label: '受付中', cls: 'success' }
}

function formatDt(dt) {
  if (!dt) return null
  return new Date(dt).toLocaleString('ja-JP', { dateStyle: 'short', timeStyle: 'short' })
}

export default function Dashboard() {
  const [polls, setPolls]     = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [copied, setCopied]   = useState(null)

  useEffect(() => {
    api.polls.list()
      .then(setPolls)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  async function deletePoll(id) {
    if (!confirm('この投票フォームを削除しますか？')) return
    try {
      await api.polls.delete(id)
      setPolls(p => p.filter(poll => poll.id !== id))
    } catch (e) {
      alert(e.message)
    }
  }

  function copyUrl(poll) {
    const url = `${location.origin}/vote/${poll.public_id}`
    navigator.clipboard.writeText(url).then(() => {
      setCopied(poll.id)
      setTimeout(() => setCopied(null), 2000)
    })
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  return (
    <main className="page">
      <div className="container">
        <div className="dash-header">
          <h1 className="dash-title">ダッシュボード</h1>
          <Link to="/polls/create" className="btn btn-primary">+ 新規作成</Link>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {polls.length === 0 ? (
          <div className="empty-state card">
            <div className="card-body text-center">
              <p className="empty-icon">📭</p>
              <p className="empty-msg">まだ投票フォームがありません。</p>
              <Link to="/polls/create" className="btn btn-primary">最初の投票を作成する</Link>
            </div>
          </div>
        ) : (
          <div className="polls-grid">
            {polls.map(poll => {
              const status = pollStatus(poll)
              return (
                <div key={poll.id} className="poll-card card">
                  <div className="card-body">
                    <div className="poll-card-top">
                      <span className={`badge badge-primary`}>{poll.voting_method_label}</span>
                      <span className={`badge badge-${status.cls}`}>{status.label}</span>
                    </div>
                    <h2 className="poll-card-title">{poll.title}</h2>
                    {poll.description && (
                      <p className="poll-card-desc">{poll.description.slice(0, 80)}{poll.description.length > 80 ? '...' : ''}</p>
                    )}
                    <div className="poll-meta">
                      <span>📋 {poll.options.length}つの選択肢</span>
                      <span>👥 {poll.vote_count}票</span>
                    </div>
                    {(poll.start_time || poll.end_time) && (
                      <div className="poll-period text-sm text-muted">
                        📅 {formatDt(poll.start_time) || 'いつでも'} 〜 {formatDt(poll.end_time) || '無期限'}
                      </div>
                    )}
                    <div className="poll-url-row">
                      <input
                        className="form-control font-mono text-sm"
                        value={`${location.origin}/vote/${poll.public_id}`}
                        readOnly
                      />
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => copyUrl(poll)}
                      >
                        {copied === poll.id ? '✓' : '📋'}
                      </button>
                    </div>
                  </div>
                  <div className="card-footer poll-actions">
                    <Link to={`/polls/${poll.id}/results`} className="btn btn-outline btn-sm">
                      📊 結果
                    </Link>
                    <Link to={`/polls/${poll.id}/edit`} className="btn btn-secondary btn-sm">
                      ✏️ 編集
                    </Link>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => deletePoll(poll.id)}
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
