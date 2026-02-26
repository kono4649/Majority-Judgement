import React from 'react'
import type { GradeDistribution } from '../types'
import { getGradeColor } from '../utils/gradeColors'

interface Props {
  distribution: GradeDistribution[]
  medianValue: number
}

export default function GradeBar({ distribution, medianValue }: Props) {
  const sorted = [...distribution].sort((a, b) => b.value - a.value)
  const totalPct = sorted.reduce((s, d) => s + d.percentage, 0)

  return (
    <div className="space-y-1">
      {/* Stacked bar */}
      <div className="flex h-8 rounded-lg overflow-hidden w-full">
        {sorted.map((d) => (
          <div
            key={d.grade_id}
            style={{
              width: `${totalPct > 0 ? (d.percentage / totalPct) * 100 : 0}%`,
              backgroundColor: getGradeColor(d.value),
              minWidth: d.percentage > 0 ? '2px' : '0',
            }}
            title={`${d.label}: ${d.count}票 (${d.percentage}%)`}
            className="transition-all"
          />
        ))}
        {totalPct === 0 && (
          <div className="w-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">
            票なし
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-xs">
        {sorted.map((d) => (
          <span key={d.grade_id} className="flex items-center gap-1">
            <span
              className="w-3 h-3 rounded-sm inline-block"
              style={{ backgroundColor: getGradeColor(d.value) }}
            />
            <span className={d.value === medianValue ? 'font-bold' : ''}>
              {d.label} {d.percentage}%
              {d.value === medianValue && ' ←中央値'}
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
