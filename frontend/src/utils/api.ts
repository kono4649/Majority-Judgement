import axios from 'axios'
import type { Poll, PollResults, Token } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
})

// Inject JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth
export const register = (data: { email: string; username: string; password: string }) =>
  api.post<Token>('/auth/register', data).then((r) => r.data)

export const login = (data: { email: string; password: string }) =>
  api.post<Token>('/auth/login', data).then((r) => r.data)

// Polls
export const listPolls = () =>
  api.get<Poll[]>('/polls').then((r) => r.data)

export const getPoll = (id: string) =>
  api.get<Poll>(`/polls/${id}`).then((r) => r.data)

export const createPoll = (data: {
  title: string
  description?: string
  options: { name: string }[]
  grades: { label: string; value: number }[]
  closes_at?: string
}) => api.post<Poll>('/polls', data).then((r) => r.data)

export const submitVote = (
  pollId: string,
  votes: Record<string, string>,
  voter_token?: string
) =>
  api
    .post<{ voter_token: string; message: string }>(`/polls/${pollId}/vote`, {
      votes,
      voter_token,
    })
    .then((r) => r.data)

export const getResults = (pollId: string) =>
  api.get<PollResults>(`/polls/${pollId}/results`).then((r) => r.data)

export const closePoll = (pollId: string) =>
  api.patch<Poll>(`/polls/${pollId}/close`).then((r) => r.data)
