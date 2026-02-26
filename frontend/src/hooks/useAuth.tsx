import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import type { User } from '../types'
import * as api from '../utils/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        setUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const token = await api.login({ email, password })
    localStorage.setItem('access_token', token.access_token)
    localStorage.setItem('user', JSON.stringify(token.user))
    setUser(token.user)
  }

  const register = async (email: string, username: string, password: string) => {
    const token = await api.register({ email, username, password })
    localStorage.setItem('access_token', token.access_token)
    localStorage.setItem('user', JSON.stringify(token.user))
    setUser(token.user)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
