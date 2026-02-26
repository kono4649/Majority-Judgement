export const GRADE_COLORS: Record<number, string> = {
  5: '#22c55e',  // 最高
  4: '#86efac',  // 優良
  3: '#fbbf24',  // 良好
  2: '#fb923c',  // 普通
  1: '#f87171',  // 不良
  0: '#dc2626',  // 不適切
}

export const getGradeColor = (value: number): string =>
  GRADE_COLORS[value] ?? '#9ca3af'
