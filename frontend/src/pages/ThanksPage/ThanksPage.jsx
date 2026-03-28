import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import './ThanksPage.css'

export default function ThanksPage() {
  const { publicId } = useParams()
  const [title, setTitle] = useState('')

  useEffect(() => {
    api.vote.getPoll(publicId)
      .then(p => setTitle(p.title))
      .catch(() => {})
  }, [publicId])

  return (
    <main className="page">
      <div className="container">
        <div className="thanks-card card">
          <div className="card-body text-center">
            <div className="thanks-icon">🎉</div>
            <h1 className="thanks-title">投票ありがとうございました！</h1>
            {title && (
              <p className="thanks-poll">「<strong>{title}</strong>」への投票が完了しました。</p>
            )}
            <div className="thanks-actions">
              <Link to={`/vote/${publicId}`} className="btn btn-secondary">
                ← 投票ページに戻る
              </Link>
              <Link to="/" className="btn btn-primary">
                🏠 ホームへ
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
