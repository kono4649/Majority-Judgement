import { useState } from 'react'
import './QuadraticVote.css'

export default function QuadraticVote({ options, methodSettings, onChange }) {
  const budget = methodSettings?.budget ?? 100
  const [votes, setVotes] = useState(Object.fromEntries(options.map(o => [o.id, 0])))

  const usedCredits = Object.values(votes).reduce((sum, v) => sum + v * v, 0)
  const remaining = budget - usedCredits

  function change(id, delta) {
    const current = votes[id] ?? 0
    const next = current + delta
    if (next < 0) return
    const newCost = next * next
    const otherCost = Object.entries(votes)
      .filter(([k]) => Number(k) !== id)
      .reduce((s, [, v]) => s + v * v, 0)
    if (newCost + otherCost > budget) return

    const next_votes = { ...votes, [id]: next }
    setVotes(next_votes)
    onChange({ votes: next_votes })
  }

  return (
    <div className="qv-vote">
      <div className="qv-budget">
        <span>予算: <strong>{budget}</strong> cr　残り: </span>
        <span className={`qv-remaining ${remaining < 10 ? 'low' : ''}`}>
          <strong>{remaining}</strong> cr
        </span>
        <span className="text-sm text-muted">（コスト = 票数²）</span>
      </div>

      {options.map(opt => {
        const v = votes[opt.id] ?? 0
        const cost = v * v
        return (
          <div key={opt.id} className="qv-row">
            <div className="qv-option-name">{opt.text}</div>
            <div className="qv-controls">
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => change(opt.id, -1)}
                disabled={v === 0}
              >－</button>
              <span className="qv-count">{v}</span>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => change(opt.id, 1)}
                disabled={remaining < (v + 1) * (v + 1) - cost}
              >＋</button>
              <span className="qv-cost text-muted text-sm">= {cost} cr</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
