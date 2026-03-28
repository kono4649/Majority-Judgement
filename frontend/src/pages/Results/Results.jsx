import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { api } from '../../api/client'
import './Results.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const BAR_COLORS = [
  '#2563eb','#7c3aed','#db2777','#dc2626',
  '#d97706','#16a34a','#0891b2','#6366f1','#f59e0b',
]

const MJ_GRADE_COLORS = {
  '拒否':'#ef4444','不良':'#f97316','許容':'#6b7280',
  '良い':'#06b6d4','とても良い':'#3b82f6','優秀':'#22c55e',
}

function ScoreLabel({ method, score, medianLabel }) {
  if (method === 'majority_judgement') {
    return <span>{medianLabel} <span className="text-muted text-xs">({Number(score).toFixed(2)})</span></span>
  }
  return <span>{typeof score === 'number' ? Number(score).toFixed(score % 1 === 0 ? 0 : 2) : score}</span>
}

function getScoreLabel(method) {
  const labels = {
    plurality: '票数', approval: '承認数', borda: 'ボルダ点', irv: '得票数',
    condorcet: '勝利数', score: '平均スコア', majority_judgement: '中央値評価',
    quadratic: '総票数', negative: '合計点',
  }
  return labels[method] || 'スコア'
}

export default function Results() {
  const { id } = useParams()
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState('')

  useEffect(() => {
    api.polls.results(id)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading-center"><div className="spinner" /></div>
  if (error)   return <main className="page"><div className="container"><div className="alert alert-danger">{error}</div></div></main>

  const { poll, options, total_votes, result, vote_url } = data
  const ranked   = result?.ranked   || []
  const details  = result?.details  || {}
  const method   = poll.voting_method

  const chartData = {
    labels: ranked.map(r => r.text),
    datasets: [{
      label: getScoreLabel(method),
      data: ranked.map(r => r.score),
      backgroundColor: ranked.map((_, i) => BAR_COLORS[i % BAR_COLORS.length]),
      borderRadius: 6,
    }],
  }
  const chartOptions = {
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: { x: { beginAtZero: true } },
    responsive: true,
    maintainAspectRatio: false,
  }

  return (
    <main className="page">
      <div className="container">
        {/* ヘッダー */}
        <div className="results-header">
          <div>
            <h1 className="results-title">📊 投票結果</h1>
            <p className="results-poll-name">{poll.title}</p>
            <span className="badge badge-primary">{poll.voting_method_label}</span>
          </div>
          <div className="results-actions">
            <a
              href={api.polls.csvUrl(id)}
              className="btn btn-success"
              download
            >⬇️ CSV</a>
            <Link to={`/polls/${id}/edit`} className="btn btn-secondary">✏️ 編集</Link>
            <Link to="/dashboard" className="btn btn-secondary">← 戻る</Link>
          </div>
        </div>

        {/* サマリー */}
        <div className="results-stats">
          <div className="stat-card">
            <div className="stat-value">{total_votes}</div>
            <div className="stat-label">総投票数</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{options.length}</div>
            <div className="stat-label">選択肢数</div>
          </div>
          <div className="stat-card url-card">
            <div className="stat-label mb-1">投票URL</div>
            <div className="url-row">
              <input className="form-control font-mono text-xs" value={vote_url} readOnly />
              <button className="btn btn-secondary btn-sm"
                onClick={() => navigator.clipboard.writeText(vote_url)}>📋</button>
            </div>
          </div>
        </div>

        {total_votes === 0 ? (
          <div className="card">
            <div className="card-body text-center text-muted">
              <p>まだ投票がありません。</p>
            </div>
          </div>
        ) : (
          <>
            {/* 勝者バナー */}
            {result?.winner_id && (
              <div className="alert alert-success winner-banner">
                🏆 <strong>勝者: </strong>
                {ranked.find(r => r.id === result.winner_id)?.text}
              </div>
            )}
            {method === 'condorcet' && details.has_cycle && (
              <div className="alert alert-warning">
                ⚠️ コンドルセ勝者は存在しません（選好の循環が検出されました）
              </div>
            )}

            {/* チャート */}
            <div className="card mb-4">
              <div className="card-header">順位グラフ</div>
              <div className="card-body">
                <div className="chart-wrap">
                  <Bar data={chartData} options={chartOptions} />
                </div>
              </div>
            </div>

            {/* 結果テーブル */}
            <div className="card mb-4">
              <div className="card-header">詳細結果</div>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>順位</th>
                      <th>選択肢</th>
                      <th>{getScoreLabel(method)}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ranked.map(item => (
                      <tr key={item.id} className={item.rank === 1 ? 'winner-row' : ''}>
                        <td>{item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : `${item.rank}位`}</td>
                        <td>{item.text}</td>
                        <td>
                          <ScoreLabel
                            method={method} score={item.score}
                            medianLabel={details.median_labels?.[String(item.id)]}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* MJ評価分布 */}
            {method === 'majority_judgement' && details.grade_distributions && (
              <div className="card mb-4">
                <div className="card-header">評価分布</div>
                <div className="card-body">
                  {ranked.map(item => {
                    const dist = details.grade_distributions[String(item.id)] || {}
                    const total = Object.values(dist).reduce((a, b) => a + b, 0)
                    return (
                      <div key={item.id} className="mj-dist-row">
                        <div className="mj-dist-name">{item.text}</div>
                        <div className="mj-dist-bar">
                          {Object.entries(MJ_GRADE_COLORS).map(([grade, color]) => {
                            const cnt = dist[grade] || 0
                            const pct = total > 0 ? (cnt / total * 100).toFixed(1) : 0
                            if (pct <= 0) return null
                            return (
                              <div
                                key={grade}
                                style={{ width: `${pct}%`, background: color }}
                                className="mj-dist-seg"
                                title={`${grade}: ${cnt}票 (${pct}%)`}
                              />
                            )
                          })}
                        </div>
                        <div className="mj-dist-labels">
                          {Object.entries(MJ_GRADE_COLORS).map(([grade, color]) => (
                            <span key={grade} className="mj-dist-label">
                              <span className="mj-dot" style={{ background: color }} />
                              {grade} {dist[grade] || 0}
                            </span>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* IRVラウンド */}
            {method === 'irv' && details.rounds?.length > 0 && (
              <div className="card mb-4">
                <div className="card-header">ラウンド別集計</div>
                <div className="table-wrap">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>ラウンド</th>
                        {ranked.map(r => <th key={r.id}>{r.text}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {details.rounds.map((round, i) => (
                        <tr key={i}>
                          <td>{i + 1}</td>
                          {ranked.map(r => (
                            <td key={r.id}>{round.counts[r.id] ?? '—'}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* コンドルセ一対比較行列 */}
            {method === 'condorcet' && details.pairwise && (
              <div className="card mb-4">
                <div className="card-header">一対比較行列</div>
                <div className="table-wrap">
                  <table className="table pairwise-table">
                    <thead>
                      <tr>
                        <th></th>
                        {ranked.map(r => <th key={r.id}>{r.text}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {ranked.map(row => (
                        <tr key={row.id}>
                          <th>{row.text}</th>
                          {ranked.map(col => {
                            if (row.id === col.id) return <td key={col.id} className="pairwise-self">—</td>
                            const ab = details.pairwise[String(row.id)]?.[String(col.id)] ?? 0
                            const ba = details.pairwise[String(col.id)]?.[String(row.id)] ?? 0
                            return (
                              <td key={col.id} className={ab > ba ? 'pairwise-win' : ab < ba ? 'pairwise-lose' : ''}>
                                {ab}:{ba}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="card-footer text-muted text-xs">行の候補が列の候補より好まれた票数</div>
              </div>
            )}

            {/* 負の投票賛否内訳 */}
            {method === 'negative' && details.positives && (
              <div className="card mb-4">
                <div className="card-header">賛否内訳</div>
                <div className="table-wrap">
                  <table className="table">
                    <thead><tr><th>選択肢</th><th>賛成</th><th>反対</th><th>合計</th></tr></thead>
                    <tbody>
                      {ranked.map(item => (
                        <tr key={item.id}>
                          <td>{item.text}</td>
                          <td className="text-success">+{details.positives[String(item.id)] || 0}</td>
                          <td className="text-danger">-{details.negatives[String(item.id)] || 0}</td>
                          <td className="font-bold">{item.score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
