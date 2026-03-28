import { Link } from 'react-router-dom'
import './Home.css'

const METHODS = [
  { name: '単記投票', desc: '最も票を得た選択肢が勝者。通常の多数決' },
  { name: '承認投票', desc: '許容できるものすべてに投票。承認数最多が勝者' },
  { name: 'ボルダ・カウント', desc: '全選択肢に順位付け。合計ポイントで比較' },
  { name: '代替投票（IRV）', desc: '優先順位付き。過半数なければ最下位除外して再集計' },
  { name: 'コンドルセ方式', desc: '一対比較で全対戦に勝つ選択肢が勝者' },
  { name: 'スコア投票', desc: '各選択肢に数値スコアを付与。平均で比較' },
  { name: 'マジョリティ・ジャッジメント', desc: '6段階評価の中央値で順位付け' },
  { name: 'クアドラティック・ボーティング', desc: 'クレジット予算内で投票。コスト = 票数²' },
  { name: '負の投票', desc: '賛成・反対を投じて差し引きで決定' },
]

export default function Home() {
  return (
    <main className="page">
      <div className="container">
        <section className="hero">
          <h1 className="hero-title">🗳️ 投票アプリ</h1>
          <p className="hero-subtitle">
            9種類の投票方式に対応した多機能投票プラットフォーム
          </p>
          <div className="hero-actions">
            <Link to="/register" className="btn btn-primary btn-lg">
              無料で始める
            </Link>
            <Link to="/login" className="btn btn-secondary btn-lg">
              ログイン
            </Link>
          </div>
        </section>

        <section className="features">
          <div className="feature-card">
            <div className="feature-icon">📋</div>
            <h3>9種類の投票方式</h3>
            <p>単記投票からマジョリティ・ジャッジメントまで多彩な集計方式をサポート</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔒</div>
            <h3>匿名・重複防止</h3>
            <p>URLを知っていれば誰でも匿名投票可能。システムで一人一票を保証</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📊</div>
            <h3>CSV出力</h3>
            <p>投票結果を作成者のみがCSV形式でダウンロード可能</p>
          </div>
        </section>

        <section className="methods-section">
          <h2 className="methods-title">対応している投票方式</h2>
          <div className="methods-grid">
            {METHODS.map(m => (
              <div key={m.name} className="method-item">
                <span className="method-check">✓</span>
                <div>
                  <strong>{m.name}</strong>
                  <p className="method-desc">{m.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  )
}
