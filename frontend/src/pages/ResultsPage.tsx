import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import type { PollResults } from '../types'
import { getResults } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'
import GradeBar from '../components/GradeBar'
import { getGradeColor } from '../utils/gradeColors'

const RANK_MEDALS = ['1位', '2位', '3位']

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const [results, setResults] = useState<PollResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    getResults(id)
      .then(setResults)
      .catch(() => setError('結果の取得に失敗しました'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <LoadingSpinner />
  if (!results || error)
    return <div className="text-center py-20 text-red-600">{error || 'エラー'}</div>

  const sorted = [...results.results].sort((a, b) => a.rank - b.rank)

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
