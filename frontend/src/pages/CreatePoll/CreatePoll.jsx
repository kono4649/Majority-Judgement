import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import './CreatePoll.css'

const VOTING_METHODS = {
  plurality:           '単記投票（多数決）',
  approval:            '承認投票',
  borda:               'ボルダ・カウント',
  irv:                 '代替投票（IRV）',
  condorcet:           'コンドルセ方式',
  score:               'スコア投票',
  majority_judgement:  'マジョリティ・ジャッジメント',
  quadratic:           'クアドラティック・ボーティング',
  negative:            '負の投票',
}

const METHOD_HELP = {
  plurality:          '最も票を得た選択肢が勝者。各投票者は1つだけ選択します。',
  approval:           '許容できる選択肢すべてに投票できます。承認数最多が勝者。',
  borda:              '全選択肢に順位付け。1位=n-1点、2位=n-2点…の合計ポイントで比較。',
  irv:                '全選択肢に優先順位付け。過半数がなければ最下位を除外して再集計。',
  condorcet:          '全選択肢に優先順位付け。一対比較で全員に勝る選択肢が勝者。',
  score:              '各選択肢にスコアを付けます。平均スコアが最高の選択肢が勝者。',
  majority_judgement: '各選択肢を「優秀〜拒否」の6段階で評価。中央値評価で順位付け。',
  quadratic:          'クレジット予算内で票を配分。コスト=票数²で支持の強度を表現。',
  negative:           '各選択肢に賛成(+1)または反対(-1)を投じられます。差し引きで決定。',
}

export default function CreatePoll() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '', description: '', voting_method: '',
    start_time: '', end_time: '',
    method_settings: {},
  })
  const [options, setOptions]   = useState(['', ''])
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [scoreMin, setScoreMin] = useState(0)
  const [scoreMax, setScoreMax] = useState(10)
  const [qvBudget, setQvBudget] = useState(100)

  function changeForm(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function changeOption(i, val) {
    setOptions(o => { const n = [...o]; n[i] = val; return n })
  }

  function addOption() {
    setOptions(o => [...o, ''])
  }

  function removeOption(i) {
    if (options.length <= 2) return
    setOptions(o => o.filter((_, idx) => idx !== i))
  }

  function buildMethodSettings() {
    if (form.voting_method === 'score')     return { min: scoreMin, max: scoreMax }
    if (form.voting_method === 'quadratic') return { budget: qvBudget }
    return {}
  }

  async function submit(e) {
    e.preventDefault()
    const cleaned = options.map(o => o.trim()).filter(Boolean)
    if (cleaned.length < 2) { setError('選択肢は2つ以上必要です。'); return }
    if (!form.voting_method) { setError('投票方式を選択してください。'); return }

    setError('')
    setLoading(true)
    try {
      await api.polls.create({
        ...form,
        options: cleaned,
        method_settings: buildMethodSettings(),
        start_time: form.start_time || null,
        end_time:   form.end_time   || null,
      })
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
        <h1 className="page-heading">投票フォーム作成</h1>

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={submit} className="poll-form">
          <div className="card mb-4">
            <div className="card-header">基本情報</div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">タイトル<span className="required">*</span></label>
                <input
                  type="text" name="title" className="form-control"
                  value={form.title} onChange={changeForm} required
                  placeholder="例: 次回のランチ場所"
                />
              </div>
              <div className="form-group">
                <label className="form-label">説明（任意）</label>
                <textarea
                  name="description" className="form-control"
                  value={form.description} onChange={changeForm} rows={2}
                  placeholder="投票の説明や注意事項など"
                />
              </div>
              <div className="form-group">
                <label className="form-label">投票方式<span className="required">*</span></label>
                <select
                  name="voting_method" className="form-control"
                  value={form.voting_method} onChange={changeForm} required
                >
                  <option value="">-- 選択してください --</option>
                  {Object.entries(VOTING_METHODS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
                {form.voting_method && (
                  <p className="form-hint">{METHOD_HELP[form.voting_method]}</p>
                )}
              </div>

              {form.voting_method === 'score' && (
                <div className="method-settings">
                  <div className="form-group">
                    <label className="form-label">スコアの範囲</label>
                    <div className="range-inputs">
                      <div>
                        <label className="form-label text-sm">最小</label>
                        <input type="number" className="form-control" value={scoreMin}
                          onChange={e => setScoreMin(Number(e.target.value))} min={0} />
                      </div>
                      <span className="range-sep">〜</span>
                      <div>
                        <label className="form-label text-sm">最大</label>
                        <input type="number" className="form-control" value={scoreMax}
                          onChange={e => setScoreMax(Number(e.target.value))} min={1} />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {form.voting_method === 'quadratic' && (
                <div className="method-settings">
                  <div className="form-group">
                    <label className="form-label">クレジット予算</label>
                    <input type="number" className="form-control" value={qvBudget}
                      onChange={e => setQvBudget(Number(e.target.value))} min={1} />
                    <p className="form-hint">各投票者が持つクレジット数（コスト = 票数²）</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="card mb-4">
            <div className="card-header">選択肢</div>
            <div className="card-body">
              {options.map((opt, i) => (
                <div key={i} className="option-row">
                  <input
                    type="text" className="form-control"
                    value={opt}
                    onChange={e => changeOption(i, e.target.value)}
                    placeholder={`選択肢 ${i + 1}`}
                  />
                  <button
                    type="button" className="btn btn-danger btn-sm btn-icon"
                    onClick={() => removeOption(i)}
                    disabled={options.length <= 2}
                  >✕</button>
                </div>
              ))}
              <button type="button" className="btn btn-secondary btn-sm mt-2"
                onClick={addOption}>
                + 選択肢を追加
              </button>
            </div>
          </div>

          <div className="card mb-4">
            <div className="card-header">有効期間（任意）</div>
            <div className="card-body">
              <div className="datetime-row">
                <div className="form-group">
                  <label className="form-label">開始日時</label>
                  <input type="datetime-local" name="start_time" className="form-control"
                    value={form.start_time} onChange={changeForm} />
                </div>
                <div className="form-group">
                  <label className="form-label">終了日時</label>
                  <input type="datetime-local" name="end_time" className="form-control"
                    value={form.end_time} onChange={changeForm} />
                </div>
              </div>
              <p className="form-hint">未設定の場合、いつでも投票を受け付けます。</p>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? '作成中...' : '✓ 作成する'}
            </button>
            <button type="button" className="btn btn-secondary btn-lg"
              onClick={() => navigate('/dashboard')}>
              キャンセル
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}
