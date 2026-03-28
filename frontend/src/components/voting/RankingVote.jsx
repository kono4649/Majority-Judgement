/**
 * ドラッグ&ドロップで順位付けする投票コンポーネント
 * ボルダ・カウント / 代替投票(IRV) / コンドルセ方式 で共用
 */
import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import './RankingVote.css'

function SortableItem({ item, rank }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: item.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : undefined,
  }

  return (
    <li ref={setNodeRef} style={style} className="rank-item" {...attributes}>
      <span className="rank-badge">{rank}</span>
      <span className="rank-text">{item.text}</span>
      <span className="drag-handle" {...listeners} title="ドラッグして並べ替え">⠿</span>
    </li>
  )
}

export default function RankingVote({ options, method, onChange }) {
  const [items, setItems] = useState(options.map(o => ({ id: o.id, text: o.text })))

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const label = {
    borda:     '全選択肢を上から好きな順に並べてください（上が1位）',
    irv:       '全選択肢を優先順位順に並べてください（上が第1希望）',
    condorcet: '全選択肢を好みの順に並べてください（上が最も好きな選択肢）',
  }[method] || '順位をつけてください'

  function handleDragEnd(event) {
    const { active, over } = event
    if (!over || active.id === over.id) return

    setItems(prev => {
      const oldIndex = prev.findIndex(i => i.id === active.id)
      const newIndex = prev.findIndex(i => i.id === over.id)
      const next = arrayMove(prev, oldIndex, newIndex)
      emitChange(next)
      return next
    })
  }

  function emitChange(current) {
    const order = current.map(i => i.id)
    if (method === 'borda') {
      const rankings = {}
      order.forEach((id, idx) => { rankings[id] = idx + 1 })
      onChange({ rankings })
    } else {
      onChange({ order })
    }
  }

  return (
    <div className="ranking-vote">
      <p className="vote-instruction">{label}</p>
      <p className="vote-instruction text-sm">ドラッグして順番を変えてください</p>
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map(i => i.id)} strategy={verticalListSortingStrategy}>
          <ul className="rank-list">
            {items.map((item, index) => (
              <SortableItem key={item.id} item={item} rank={index + 1} />
            ))}
          </ul>
        </SortableContext>
      </DndContext>
    </div>
  )
}
