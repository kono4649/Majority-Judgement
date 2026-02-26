import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import type { Poll } from '../types'
import { listPolls } from '../utils/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function HomePage() {
  const [polls, setPolls] = useState<Poll[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listPolls()
      .then(setPolls)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Majority Judgement 投票
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          各選択肢を多段階で評価し、中央値に基づいてランキングを決定する、より公正な投票方式です。
        </p>
        <Link
          to="/register"
          className="mt-6 inline-block bg-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition-colors"
        >
          投票を作成する
        </Link>
      </div>

      {/* Poll list */}
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        進行中の投票 ({polls.filter((p) => p.is_open).length})
      </h2>

      {polls.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          まだ投票がありません。最初の投票を作成しましょう！
        </div>
      ) : (
        <div className="grid gap-4">
          {polls.map((poll) => (
            <div
              key={poll.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">{poll.title}</h3>
                  {poll.description && (
                    <p className="text-gray-500 text-sm mt-1 line-clamp-2">{poll.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>{poll.options.length} 選択肢</span>
                    <span>{new Date(poll.created_at).toLocaleDateString('ja-JP')}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium ${
                      poll.is_open
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {poll.is_open ? '受付中' : '終了'}
                  </span>
                  <div className="flex gap-2">
                    {poll.is_open && (
                      <Link
                        to={`/polls/${poll.id}/vote`}
                        className="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        投票する
                      </Link>
                    )}
                    <Link
                      to={`/polls/${poll.id}/results`}
                      className="text-sm border border-indigo-600 text-indigo-600 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors"
                    >
                      結果
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
