import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { Poll } from '../types'
import { getPoll, submitVote } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { getGradeColor } from '../utils/gradeColors'

const VOTER_TOKEN_KEY = 'mj_voter_token'

function getOrCreateVoterToken(): string {
  let token = localStorage.getItem(VOTER_TOKEN_KEY)
  if (!token) {
    token = crypto.randomUUID()
    localStorage.setItem(VOTER_TOKEN_KEY, token)
  }
  return token
}

export default function VotePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [poll, setPoll] = useState<Poll | null>(null)
  const [loading, setLoading] = useState(true)
  const [votes, setVotes] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getPoll(id)
      .then(setPoll)
      .catch(() => setError('投票が見つかりません'))
      .finally(() => setLoading(false))
  }, [id])

  const sortedGrades = poll
    ? [...poll.grades].sort((a, b) => b.value - a.value)
    : []

  const allVoted =
    poll !== null && poll.options.every((opt) => votes[opt.id] !== undefined)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!poll || !allVoted) return
    setError('')
    setSubmitting(true)
    try {
      const voter_token = getOrCreateVoterToken()
      await submitVote(poll.id, votes, voter_token)
      navigate(`/polls/${poll.id}/results`)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '投票に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSpinner />
  if (!poll)
    return (
      <div className="text-center py-20 text-red-600">{error || '投票が見つかりません'}</div>
    )
  if (!poll.is_open)
    return (
      <div className="text-center py-20">
        <p className="text-gray-600 mb-4">この投票は終了しています</p>
        <button
          onClick={() => navigate(`/polls/${poll.id}/results`)}
          className="bg-indigo-600 text-white px-6 py-2 rounded-lg"
        >
          結果を見る
        </button>
      </div>
    )

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{poll.title}</h1>
      {poll.description && (
        <p className="text-gray-600 mb-6">{poll.description}</p>
      )}

      <p className="text-sm text-gray-500 mb-6">
        各選択肢に対して評価を選んでください。全ての選択肢に評価が必要です。
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Grade header */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {/* Header row */}
          <div className="grid border-b border-gray-100 bg-gray-50 p-3"
            style={{ gridTemplateColumns: `200px repeat(${sortedGrades.length}, 1fr)` }}>
            <span className="text-sm font-medium text-gray-700">選択肢</span>
            {sortedGrades.map((g) => (
              <span
                key={g.id}
                className="text-center text-xs font-medium text-gray-700 px-1"
                style={{ color: getGradeColor(g.value) }}
              >
                {g.label}
              </span>
            ))}
          </div>

          {/* Option rows */}
          {poll.options.map((opt, i) => (
            <div
              key={opt.id}
              className={`grid items-center p-3 ${i % 2 === 0 ? '' : 'bg-gray-50'}`}
              style={{ gridTemplateColumns: `200px repeat(${sortedGrades.length}, 1fr)` }}
            >
              <span className="text-sm font-medium text-gray-900 pr-3 truncate">{opt.name}</span>
              {sortedGrades.map((g) => (
                <label
                  key={g.id}
                  className="flex justify-center cursor-pointer"
                >
                  <input
                    type="radio"
                    name={`option-${opt.id}`}
                    value={g.id}
                    checked={votes[opt.id] === g.id}
                    onChange={() => setVotes({ ...votes, [opt.id]: g.id })}
                    className="sr-only"
                  />
                  <span
                    className={`w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${
                      votes[opt.id] === g.id
                        ? 'border-transparent scale-110'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                    style={
                      votes[opt.id] === g.id
                        ? { backgroundColor: getGradeColor(g.value) }
                        : {}
                    }
                  >
                    {votes[opt.id] === g.id && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                        <path d="M10 3L5 8.5 2 5.5" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    )}
                  </span>
                </label>
              ))}
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            {Object.keys(votes).length} / {poll.options.length} 選択肢を評価済み
          </span>
          <button
            type="submit"
            disabled={!allVoted || submitting}
            className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? '投票中...' : '投票する'}
          </button>
        </div>
      </form>
    </div>
  )
}
