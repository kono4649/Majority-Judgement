import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import PluralityVote         from '../../components/voting/PluralityVote'
import ApprovalVote          from '../../components/voting/ApprovalVote'
import RankingVote           from '../../components/voting/RankingVote'
import ScoreVote             from '../../components/voting/ScoreVote'
import MajorityJudgementVote from '../../components/voting/MajorityJudgementVote'
import QuadraticVote         from '../../components/voting/QuadraticVote'
import NegativeVote          from '../../components/voting/NegativeVote'
import './VotePage.css'

function formatDt(dt) {
  if (!dt) return null
  return new Date(dt).toLocaleString('ja-JP', { dateStyle: 'long', timeStyle: 'short' })
}

export default function VotePage() {
  const { publicId } = useParams()
  const navigate = useNavigate()

  const [poll, setPoll]             = useState(null)
  const [status, setStatus]         = useState(null)
  const [voteData, setVoteData]     = useState(null)
  const [error, setError]           = useState('')
  const [submitError, setSubmitError] = useState('')
  const [loading, setLoading]       = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    Promise.all([api.vote.getPoll(publicId), api.vote.getStatus(publicId)])
      .then(([p, s]) => { setPoll(p); setStatus(s) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [publicId])

  async function submit(e) {
    e.preventDefault()
    if (!voteData) { setSubmitError('投票内容を入力してください。'); return }

    // MJ: 全選択肢の評価必須チェック
    if (poll.voting_method === 'majority_judgement') {
      const graded = Object.keys(voteData.grades || {}).length
      if (graded < poll.options.length) {
        setSubmitError('すべての選択肢を評価してください。'); return
      }
    }

    setSubmitError('')
    setSubmitting(true)
    try {
      await api.vote.submit(publicId, voteData)
      navigate(`/vote/${publicId}/thanks`)
    } catch (err) {
      setSubmitError(err.message)
      setSubmitting(false)
    }
  }

  function renderVoteComponent() {
    const method = poll.voting_method
    const props = {
      options: poll.options,
      methodSettings: poll.method_settings,
      onChange: setVoteData,
    }
    const rankMethods = ['borda', 'irv', 'condorcet']
    if (method === 'plurality')          return <PluralityVote {...props} />
    if (method === 'approval')           return <ApprovalVote  {...props} />
    if (rankMethods.includes(method))    return <RankingVote   {...props} method={method} />
    if (method === 'score')              return <ScoreVote      {...props} />
    if (method === 'majority_judgement') return <MajorityJudgementVote {...props} />
    if (method === 'quadratic')          return <QuadraticVote {...props} />
    if (method === 'negative')           return <NegativeVote  {...props} />
    return null
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>

  if (error) return (
    <main className="page">
      <div className="container">
        <div className="alert alert-danger">⚠️ {error}</div>
      </div>
    </main>
  )

  return (
    <main className="page">
      <div className="container">
        <div className="vote-wrap">
          {/* 投票フォームヘッダー */}
          <div className="card vote-header-card">
            <div className="card-body">
              <h1 className="vote-title">{poll.title}</h1>
              {poll.description && <p className="vote-desc">{poll.description}</p>}
              <div className="vote-meta">
                <span className="badge badge-primary">{poll.voting_method_label}</span>
                {poll.end_time && (
                  <span className="text-sm text-muted">締切: {formatDt(poll.end_time)}</span>
                )}
              </div>
            </div>
          </div>

          {/* 投票済み */}
          {status?.already_voted && (
            <div className="card">
              <div className="card-body text-center">
                <div className="big-icon">✅</div>
                <p className="big-msg">すでにこの投票に参加済みです。</p>
                <p className="text-muted">ご協力ありがとうございました。</p>
              </div>
            </div>
          )}

          {/* 期間外 */}
          {!status?.already_voted && !status?.is_active && (
            <div className="card">
              <div className="card-body text-center">
                <div className="big-icon">⏰</div>
                <p className="big-msg">
                  {poll.start_time && new Date(poll.start_time) > new Date()
                    ? 'この投票はまだ開始されていません。'
                    : 'この投票は終了しました。'}
                </p>
              </div>
            </div>
          )}

          {/* 投票フォーム */}
          {!status?.already_voted && status?.is_active && (
            <form onSubmit={submit}>
              <div className="card">
                <div className="card-body">
                  {submitError && <div className="alert alert-danger">{submitError}</div>}
                  {renderVoteComponent()}
                </div>
                <div className="card-footer">
                  <button
                    type="submit"
                    className="btn btn-primary btn-lg"
                    disabled={submitting}
                  >
                    {submitting ? '送信中...' : '✓ 投票する'}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  )
}
