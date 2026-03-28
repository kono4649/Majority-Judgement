import { useState } from 'react'
import './PluralityVote.css'

export default function PluralityVote({ options, onChange }) {
  const [selected, setSelected] = useState(null)

  function select(id) {
    setSelected(id)
    onChange({ option_id: id })
  }

  return (
    <div className="plurality-vote">
      <p className="vote-instruction">1つの選択肢を選んでください</p>
      {options.map(opt => (
        <label
          key={opt.id}
          className={`vote-option ${selected === opt.id ? 'selected' : ''}`}
        >
          <input
            type="radio"
            name="plurality"
            value={opt.id}
            checked={selected === opt.id}
            onChange={() => select(opt.id)}
          />
          <span className="vote-option-text">{opt.text}</span>
        </label>
      ))}
    </div>
  )
}
