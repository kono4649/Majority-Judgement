import { useState } from 'react'
import './NegativeVote.css'

export default function NegativeVote({ options, onChange }) {
  const [votes, setVotes] = useState(Object.fromEntries(options.map(o => [o.id, 0])))

  function select(id, val) {
    const next = { ...votes, [id]: val }
    setVotes(next)
    onChange({ votes: next })
  }

  return (
    <div className="negative-vote">
      <p className="vote-instruction">
        各選択肢に賛成(+1)・棄権(0)・反対(-1)を選んでください
      </p>
      {options.map(opt => {
        const v = votes[opt.id] ?? 0
        return (
          <div key={opt.id} className="neg-row">
            <span className="neg-option-name">{opt.text}</span>
            <div className="neg-btns">
              <button
                type="button"
                className={`neg-btn neg-pos ${v === 1 ? 'active' : ''}`}
                onClick={() => select(opt.id, v === 1 ? 0 : 1)}
              >
                👍 賛成 (+1)
              </button>
              <button
                type="button"
                className={`neg-btn neg-neutral ${v === 0 ? 'active' : ''}`}
                onClick={() => select(opt.id, 0)}
              >
                棄権
              </button>
              <button
                type="button"
                className={`neg-btn neg-neg ${v === -1 ? 'active' : ''}`}
                onClick={() => select(opt.id, v === -1 ? 0 : -1)}
              >
                👎 反対 (-1)
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
