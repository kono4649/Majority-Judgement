import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { Poll, PollResults } from '../types'
import { getResults, getPoll, updatePoll, closePoll } from '../utils/api'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from '../components/LoadingSpinner'
import GradeBar from '../components/GradeBar'
import { getGradeColor } from '../utils/gradeColors'

const RANK_MEDALS = ['1位', '2位', '3位']

function toLocalDatetimeValue(isoString: string | null): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  const pad = (n: number) => String(n).padStart(2, '0')
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}`
  )
}

function PollManagement({ poll, onUpdated }: { poll: Poll; onUpdated: (p: Poll) => void }) {
  const [deadlineValue, setDeadlineValue] = useState(toLocalDatetimeValue(poll.closes_at))
  const [isPublic, setIsPublic] = useState(poll.is_public)
  const [saving, setSaving] = useState(false)
  const [closing, setClosing] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saveSuccess, setSaveSuccess] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    setSaveError('')
    setSaveSuccess(false)
    try {
      const closes_at = deadlineValue ? new Date(deadlineValue).toISOString() : null
      const updated = await updatePoll(poll.id, { closes_at, is_public: isPublic })
      onUpdated(updated)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch {
      setSaveError('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  const handleClose = async () => {
    if (!window.confirm('この投票を終了しますか？終了後は再開できません。')) return
    setClosing(true)
    try {
      const updated = await closePoll(poll.id)
      onUpdated(updated)
    } catch {
      setSaveError('投票の終了に失敗しました')
    } finally {
      setClosing(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-8">
      <h2 className="text-base font-semibold text-gray-800 mb-4">投票の管理</h2>

      <div className="space-y-4">
        {/* Deadline */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            締め切り日時（任意）
          </label>
          <div className="flex gap-2 items-center">
            <input
              type="datetime-local"
              value={deadlineValue}
              onChange={(e) => setDeadlineValue(e.target.value)}
              disabled={!poll.is_open}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-gray-100 disabled:text-gray-400"
            />
            {deadlineValue && (
              <button
                type="button"
                onClick={() => setDeadlineValue('')}
                disabled={!poll.is_open}
                className="text-xs text-gray-400 hover:text-gray-600 disabled:cursor-not-allowed"
              >
                クリア
              </button>
            )}
          </div>
          {!poll.is_open && (
            <p className="text-xs text-gray-400 mt-1">投票が終了しているため変更できません</p>
          )}
        </div>

        {/* Visibility */}
        <div>
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="w-4 h-4 rounded accent-indigo-600"
            />
            <span className="text-sm font-medium text-gray-700">
              投票シートを公開する
            </span>
          </label>
          <p className="text-xs text-gray-400 mt-1 ml-6">
            {isPublic
              ? '一覧ページに表示され、誰でも投票できます'
              : '一覧には表示されません。URLを知っている人のみ投票できます'}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3 pt-1">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !poll.is_open}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? '保存中...' : '保存する'}
          </button>
          {poll.is_open && (
            <button
              type="button"
              onClick={handleClose}
              disabled={closing}
              className="border border-red-400 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {closing ? '処理中...' : '投票を終了する'}
            </button>
          )}
          {saveSuccess && (
            <span className="text-sm text-green-600">保存しました</span>
          )}
          {saveError && (
            <span className="text-sm text-red-600">{saveError}</span>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const [poll, setPoll] = useState<Poll | null>(null)
  const [results, setResults] = useState<PollResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    Promise.all([getResults(id), getPoll(id)])
      .then(([r, p]) => {
        setResults(r)
        setPoll(p)
      })
      .catch(() => setError('結果の取得に失敗しました'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner />
  if (!results || error)
    return <div className="text-center py-20 text-red-600">{error || 'エラー'}</div>

  const sorted = [...results.results].sort((a, b) => a.rank - b.rank)
  const isCreator = user && poll && user.id === poll.creator_id

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold text-gray-900">{results.title}</h1>
        <Link
          to={`/polls/${id}/vote`}
          className="text-sm text-indigo-600 hover:underline"
        >
          投票する
        </Link>
      </div>
      <p className="text-gray-500 text-sm mb-8">
        投票者数: {results.total_voters}人
      </p>

      {/* Poll management (creator only) */}
      {isCreator && poll && (
        <PollManagement poll={poll} onUpdated={setPoll} />
      )}

      {/* Ranking summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {sorted.slice(0, 3).map((opt, i) => (
          <div
            key={opt.option_id}
            className="bg-white rounded-xl border border-gray-200 p-4 text-center shadow-sm"
          >
            <div className="text-3xl mb-1">{['🥇','🥈','🥉'][i]}</div>
            <div className="font-semibold text-gray-900">{opt.name}</div>
            <div
              className="text-sm font-medium mt-1"
              style={{ color: getGradeColor(opt.median_grade.value) }}
            >
              中央値: {opt.median_grade.label}
            </div>
          </div>
        ))}
      </div>

      {/* Detailed results */}
      <h2 className="text-lg font-semibold text-gray-800 mb-4">詳細結果</h2>
      <div className="space-y-5">
        {sorted.map((opt) => (
          <div key={opt.option_id} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-500 w-8">
                  {RANK_MEDALS[opt.rank - 1] ?? `${opt.rank}位`}
                </span>
                <span className="font-semibold text-gray-900">{opt.name}</span>
              </div>
              <div className="text-right">
                <span
                  className="text-sm font-medium px-2 py-0.5 rounded"
                  style={{
                    backgroundColor: getGradeColor(opt.median_grade.value) + '22',
                    color: getGradeColor(opt.median_grade.value),
                  }}
                >
                  中央値: {opt.median_grade.label}
                </span>
                <div className="text-xs text-gray-400 mt-0.5">{opt.total_votes}票</div>
              </div>
            </div>

            <GradeBar
              distribution={opt.grade_distribution}
              medianValue={opt.median_grade.value}
            />
          </div>
        ))}
      </div>

      {/* Algorithm explanation */}
      <div className="mt-10 bg-indigo-50 rounded-xl p-5 border border-indigo-100">
        <h3 className="font-semibold text-indigo-900 mb-2">算出方法について</h3>
        <p className="text-sm text-indigo-800 leading-relaxed">
          Majority Judgement (MJ) では、各選択肢への全評価を並べた時の<strong>中央値</strong>を基準に順位を決定します。
          中央値が同じ場合は、中央値と一致する評価を1つずつ取り除いていき、新しい中央値で比較する<strong>タイブレーク</strong>を行います。
        </p>
      </div>
    </div>
  )
}
