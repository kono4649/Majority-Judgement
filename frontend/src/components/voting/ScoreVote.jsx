import { useState } from 'react'
import './ScoreVote.css'

export default function ScoreVote({ options, methodSettings, onChange }) {
  const min = methodSettings?.min ?? 0
  const max = methodSettings?.max ?? 10
  const mid = Math.round((min + max) / 2)

  const [scores, setScores] = useState(
    Object.fromEntries(options.map(o => [o.id, mid]))
  )

  function update(id, value) {
    const next = { ...scores, [id]: Number(value) }
    setScores(next)
    onChange({ scores: next })
  }

  return (
    <div className="score-vote">
      <p className="vote-instruction">各選択肢にスコアを付けてください（{min}〜{max}）</p>
      {options.map(opt => (
        <div key={opt.id} className="score-row">
          <div className="score-header">
            <span className="score-label">{opt.text}</span>
            <span className="score-value">{scores[opt.id]}</span>
          </div>
          <div className="score-range-row">
            <span className="score-min">{min}</span>
            <input
              type="range"
              min={min}
              max={max}
              value={scores[opt.id]}
              onChange={e => update(opt.id, e.target.value)}
              className="score-slider"
            />
            <span className="score-max">{max}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
