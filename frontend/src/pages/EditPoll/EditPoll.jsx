import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import './EditPoll.css'

const VOTING_METHODS = {
  plurality: '単記投票（多数決）', approval: '承認投票', borda: 'ボルダ・カウント',
  irv: '代替投票（IRV）', condorcet: 'コンドルセ方式', score: 'スコア投票',
  majority_judgement: 'マジョリティ・ジャッジメント', quadratic: 'クアドラティック・ボーティング',
  negative: '負の投票',
}

export default function EditPoll() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [poll, setPoll]       = useState(null)
  const [form, setForm]       = useState({})
  const [options, setOptions] = useState([])
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)

  useEffect(() => {
    api.polls.get(id)
      .then(p => {
        setPoll(p)
        setForm({
          title: p.title,
          description: p.description || '',
          start_time: p.start_time || '',
          end_time:   p.end_time   || '',
        })
        setOptions(p.options.map(o => o.text))
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  function changeForm(e) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  function changeOption(i, val) {
    setOptions(o => { const n = [...o]; n[i] = val; return n })
  }

  function addOption() { setOptions(o => [...o, '']) }
  function removeOption(i) {
    if (options.length <= 2) return
    setOptions(o => o.filter((_, idx) => idx !== i))
  }

  async function submit(e) {
    e.preventDefault()
    const cleaned = options.map(o => o.trim()).filter(Boolean)
    if (cleaned.length < 2) { setError('選択肢は2つ以上必要です。'); return }
    setError('')
    setSaving(true)
    try {
      await api.polls.update(id, {
        ...form,
        options: cleaned,
        method_settings: poll.method_settings || {},
        start_time: form.start_time || null,
        end_time:   form.end_time   || null,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading-center"><div className="spinner" /></div>
  if (!poll && error) return (
    <main className="page"><div className="container"><div className="alert alert-danger">{error}</div></div></main>
  )

  const hasVotes = poll.vote_count > 0

  return (
    <main className="page">
      <div className="container">
        <h1 className="page-heading">投票フォーム編集</h1>

        {hasVotes && (
          <div className="alert alert-warning">
            ⚠️ すでに <strong>{poll.vote_count}票</strong> が投じられています。
            選択肢のテキストのみ変更可能で、追加・削除はできません。
          </div>
        )}
        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={submit} className="poll-form">
          <div className="card mb-4">
            <div className="card-header">基本情報</div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">タイトル</label>
                <input type="text" name="title" className="form-control"
                  value={form.title} onChange={changeForm} required />
              </div>
              <div className="form-group">
                <label className="form-label">説明</label>
                <textarea name="description" className="form-control"
                  value={form.description} onChange={changeForm} rows={2} />
              </div>
              <div className="form-group">
                <label className="form-label">投票方式</label>
                <input type="text" className="form-control"
                  value={VOTING_METHODS[poll.voting_method] || poll.voting_method}
                  disabled />
                <p className="form-hint">投票方式は変更できません。</p>
              </div>
            </div>
          </div>

          <div className="card mb-4">
            <div className="card-header">選択肢</div>
            <div className="card-body">
              {options.map((opt, i) => (
                <div key={i} className="option-row">
                  <input type="text" className="form-control"
                    value={opt} onChange={e => changeOption(i, e.target.value)}
                    placeholder={`選択肢 ${i + 1}`} />
                  {!hasVotes && (
                    <button type="button" className="btn btn-danger btn-sm btn-icon"
                      onClick={() => removeOption(i)} disabled={options.length <= 2}>✕</button>
                  )}
                </div>
              ))}
              {!hasVotes && (
                <button type="button" className="btn btn-secondary btn-sm mt-2"
                  onClick={addOption}>+ 選択肢を追加</button>
              )}
            </div>
          </div>

          <div className="card mb-4">
            <div className="card-header">有効期間</div>
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
              <p className="form-hint">変更は即座に反映されます。</p>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
              {saving ? '保存中...' : '✓ 保存する'}
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
