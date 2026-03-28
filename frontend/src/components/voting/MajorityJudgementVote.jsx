import { useState } from 'react'
import './MajorityJudgementVote.css'

const GRADES = ['拒否', '不良', '許容', '良い', 'とても良い', '優秀']
const GRADE_COLORS = ['#ef4444', '#f97316', '#6b7280', '#06b6d4', '#3b82f6', '#22c55e']

export default function MajorityJudgementVote({ options, onChange }) {
  const [grades, setGrades] = useState({})

  function select(optId, grade) {
    const next = { ...grades, [optId]: grade }
    setGrades(next)
    onChange({ grades: next })
  }

  return (
    <div className="mj-vote">
      <p className="vote-instruction">
        各選択肢を6段階で評価してください（全選択肢の評価が必要です）
      </p>
      {options.map(opt => (
        <div key={opt.id} className="mj-row">
          <div className="mj-option-name">{opt.text}</div>
          <div className="mj-grades">
            {GRADES.map((grade, i) => (
              <button
                key={grade}
                type="button"
                className={`mj-btn ${grades[opt.id] === grade ? 'mj-active' : ''}`}
                style={{
                  '--grade-color': GRADE_COLORS[i],
                  background: grades[opt.id] === grade ? GRADE_COLORS[i] : undefined,
                }}
                onClick={() => select(opt.id, grade)}
              >
                {grade}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
