import { useState } from 'react'
import './ApprovalVote.css'

export default function ApprovalVote({ options, onChange }) {
  const [selected, setSelected] = useState(new Set())

  function toggle(id) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      onChange({ option_ids: [...next] })
      return next
    })
  }

  return (
    <div className="approval-vote">
      <p className="vote-instruction">許容できる選択肢をすべて選んでください（複数可）</p>
      {options.map(opt => (
        <label
          key={opt.id}
          className={`vote-option ${selected.has(opt.id) ? 'selected' : ''}`}
        >
          <input
            type="checkbox"
            checked={selected.has(opt.id)}
            onChange={() => toggle(opt.id)}
          />
          <span className="vote-option-text">{opt.text}</span>
        </label>
      ))}
    </div>
  )
}
