import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import './Register.css'

export default function Register() {
  const [form, setForm]     = useState({ email: '', password: '', password_confirm: '' })
  const [error, setError]   = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  function change(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.auth.register(form)
      setSuccess(res.message)
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
            <h1 className="auth-title">新規登録</h1>

            {success ? (
              <div>
                <div className="alert alert-success">{success}</div>
                <div className="text-center">
                  <Link to="/login" className="btn btn-primary">ログインへ</Link>
                </div>
              </div>
            ) : (
              <>
                {error && <div className="alert alert-danger">{error}</div>}
                <form onSubmit={submit}>
                  <div className="form-group">
                    <label className="form-label">
                      メールアドレス<span className="required">*</span>
                    </label>
                    <input
                      type="email" name="email" className="form-control"
                      value={form.email} onChange={change} required autoFocus
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      パスワード<span className="required">*</span>
                    </label>
                    <input
                      type="password" name="password" className="form-control"
                      value={form.password} onChange={change} required
                      placeholder="8文字以上、大小英字・数字・記号を含む"
                    />
                    <p className="form-hint">
                      大文字・小文字・数字・記号（!@#$%など）をそれぞれ1文字以上含む8文字以上
                    </p>
                  </div>
                  <div className="form-group">
                    <label className="form-label">
                      パスワード（確認）<span className="required">*</span>
                    </label>
                    <input
                      type="password" name="password_confirm" className="form-control"
                      value={form.password_confirm} onChange={change} required
                    />
                  </div>
                  <button
                    type="submit" className="btn btn-primary w-full"
                    disabled={loading}
                  >
                    {loading ? '送信中...' : '登録する'}
                  </button>
                </form>
                <p className="auth-footer">
                  すでにアカウントをお持ちの方は <Link to="/login">ログイン</Link>
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
