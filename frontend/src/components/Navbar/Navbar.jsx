import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import './Navbar.css'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">
          🗳️ 投票アプリ
        </Link>

        <button
          className="navbar-toggle"
          onClick={() => setMenuOpen(o => !o)}
          aria-label="メニュー"
        >
          <span />
          <span />
          <span />
        </button>

        <div className={`navbar-menu ${menuOpen ? 'is-open' : ''}`}>
          {user ? (
            <>
              <Link to="/dashboard" className="navbar-link" onClick={() => setMenuOpen(false)}>
                ダッシュボード
              </Link>
              <Link to="/polls/create" className="navbar-link" onClick={() => setMenuOpen(false)}>
                + 新規作成
              </Link>
              <span className="navbar-user">{user.email}</span>
              <button className="btn btn-secondary btn-sm" onClick={handleLogout}>
                ログアウト
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar-link" onClick={() => setMenuOpen(false)}>
                ログイン
              </Link>
              <Link
                to="/register"
                className="btn btn-primary btn-sm"
                onClick={() => setMenuOpen(false)}
              >
                新規登録
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
