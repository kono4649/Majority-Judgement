export interface User {
  id: string
  email: string
  username: string
}

export interface Token {
  access_token: string
  token_type: string
  user: User
}

export interface Grade {
  id: string
  label: string
  value: number
}

export interface Option {
  id: string
  name: string
  display_order: number
}

export interface Poll {
  id: string
  title: string
  description: string | null
  is_open: boolean
  is_public: boolean
  created_at: string
  closes_at: string | null
  creator_id: string
  options: Option[]
  grades: Grade[]
}

export interface GradeDistribution {
  grade_id: string
  label: string
  value: number
  count: number
  percentage: number
}

export interface OptionResult {
  option_id: string
  name: string
  median_grade: Grade
  median_value: number
  rank: number
  total_votes: number
  grade_distribution: GradeDistribution[]
}

export interface PollResults {
  poll_id: string
  title: string
  total_voters: number
  results: OptionResult[]
}
