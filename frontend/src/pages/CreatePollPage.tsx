import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPoll } from '../utils/api'

const DEFAULT_GRADES = [
  { label: '最高', value: 5 },
  { label: '優良', value: 4 },
  { label: '良好', value: 3 },
  { label: '普通', value: 2 },
  { label: '不良', value: 1 },
  { label: '不適切', value: 0 },
]

export default function CreatePollPage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [options, setOptions] = useState(['', ''])
  const [grades, setGrades] = useState(DEFAULT_GRADES)
  const [closesAt, setClosesAt] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const addOption = () => setOptions([...options, ''])
  const removeOption = (i: number) => setOptions(options.filter((_, idx) => idx !== i))
  const updateOption = (i: number, val: string) =>
    setOptions(options.map((o, idx) => (idx === i ? val : o)))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const validOptions = options.filter((o) => o.trim())
    if (validOptions.length < 2) {
      setError('最低2つの選択肢を入力してください')
      return
    }

    setLoading(true)
    try {
      const poll = await createPoll({
        title,
        description: description || undefined,
        options: validOptions.map((name) => ({ name })),
        grades,
        closes_at: closesAt || undefined,
      })
      navigate(`/polls/${poll.id}/vote`)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? '投票の作成に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">新しい投票を作成</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            タイトル <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="例：次回のランチはどこがいい？"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">説明（任意）</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="投票の詳細を説明してください"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>

        {/* Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            選択肢 <span className="text-red-500">*</span>
          </label>
          <div className="space-y-2">
            {options.map((opt, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={opt}
                  onChange={(e) => updateOption(i, e.target.value)}
                  placeholder={`選択肢 ${i + 1}`}
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {options.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeOption(i)}
                    className="text-red-500 hover:text-red-700 px-2"
                  >
                    削除
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addOption}
            className="mt-2 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            + 選択肢を追加
          </button>
        </div>

        {/* Grades */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">評価スケール</label>
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            {grades.map((g, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="w-4 h-4 rounded-sm" style={{
                  backgroundColor: ['#22c55e','#86efac','#fbbf24','#fb923c','#f87171','#dc2626'][i] ?? '#9ca3af'
                }} />
                <input
                  type="text"
                  value={g.label}
                  onChange={(e) =>
                    setGrades(grades.map((gr, gi) => gi === i ? { ...gr, label: e.target.value } : gr))
                  }
                  className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm"
                />
                <span className="text-gray-400 text-xs">値: {g.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Close date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">締め切り日時（任意）</label>
          <input
            type="datetime-local"
            value={closesAt}
            onChange={(e) => setClosesAt(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? '作成中...' : '投票を作成する'}
        </button>
      </form>
    </div>
  )
}
