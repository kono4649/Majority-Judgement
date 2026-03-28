import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import './Login.css'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()

  const [form, setForm]   = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const activated  = params.get('activated') === '1'
  const tokenError = params.get('error') === 'invalid_token'

  function change(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page">
      <div className="container">
        <div className="auth-card card">
          <div className="card-body">
            <h1 className="auth-title">ログイン</h1>

            {activated  && <div className="alert alert-success">✅ アカウントが有効化されました！</div>}
            {tokenError && <div className="alert alert-danger">無効または期限切れのアクティベーションリンクです。</div>}
            {error      && <div className="alert alert-danger">{error}</div>}

            <form onSubmit={submit}>
              <div className="form-group">
                <label className="form-label">メールアドレス</label>
                <input
                  type="email" name="email" className="form-control"
                  value={form.email} onChange={change} required autoFocus
                />
              </div>
              <div className="form-group">
                <label className="form-label">パスワード</label>
                <input
                  type="password" name="password" className="form-control"
                  value={form.password} onChange={change} required
                />
              </div>
              <button
                type="submit" className="btn btn-primary w-full"
                disabled={loading}
              >
                {loading ? 'ログイン中...' : 'ログイン'}
              </button>
            </form>
            <p className="auth-footer">
              アカウントをお持ちでない方は <Link to="/register">新規登録</Link>
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
