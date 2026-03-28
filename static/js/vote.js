/**
 * 投票フォーム JavaScript
 * 各投票方式のUIロジックとフォーム送信処理
 */

// ===== 単記投票 =====
function selectPlurality(el, optionId) {
  document.querySelectorAll('.vote-option').forEach(e => e.classList.remove('selected'));
  el.classList.add('selected');
  const radio = el.querySelector('input[type="radio"]');
  if (radio) radio.checked = true;
}

// ===== 承認投票 =====
function toggleApproval(el, optionId) {
  el.classList.toggle('selected');
  const cb = el.querySelector('input[type="checkbox"]');
  if (cb) cb.checked = !cb.checked;
}

// ===== MJグレード選択 =====
function selectMJGrade(btn) {
  const optId = btn.dataset.id;
  // 同じ選択肢の他ボタンをリセット
  document.querySelectorAll(`.mj-btn[data-id="${optId}"]`).forEach(b => {
    b.classList.remove('active-grade');
    // アウトラインに戻す
    b.className = b.className.replace(/\bbtn-(?!outline)[a-z-]+\b/g, '').trim();
    if (!b.className.includes('btn-outline-')) {
      const colorClass = Array.from(b.classList).find(c => c.startsWith('btn-'));
      if (colorClass) {
        b.classList.remove(colorClass);
        b.classList.add(colorClass.replace('btn-', 'btn-outline-'));
      }
    }
  });
  // 選択したボタンをアクティブに
  btn.classList.add('active-grade');
  const outlineClass = Array.from(btn.classList).find(c => c.startsWith('btn-outline-'));
  if (outlineClass) {
    btn.classList.remove(outlineClass);
    btn.classList.add(outlineClass.replace('btn-outline-', 'btn-'));
  }
}

// ===== 負の投票 =====
function selectNegative(btn) {
  const optId = btn.dataset.id;
  const val = parseInt(btn.dataset.val);
  // 同グループをリセット
  document.querySelectorAll(`.negative-btn[data-id="${optId}"]`).forEach(b => {
    b.classList.remove('active-positive', 'active-neutral', 'active-negative');
  });
  // 選択
  if (val === 1) btn.classList.add('active-positive');
  else if (val === 0) btn.classList.add('active-neutral');
  else btn.classList.add('active-negative');
}

// ===== フォーム送信 =====
function prepareVote(method) {
  let voteData = null;

  try {
    if (method === 'plurality') {
      const selected = document.querySelector('input[name="plurality"]:checked');
      if (!selected) { alert('選択肢を1つ選んでください。'); return false; }
      voteData = { option_id: parseInt(selected.value) };

    } else if (method === 'approval') {
      const checked = Array.from(document.querySelectorAll('.vote-option.selected input[type="checkbox"]'))
                          .map(cb => parseInt(cb.value));
      if (checked.length === 0) { alert('少なくとも1つの選択肢を選んでください。'); return false; }
      voteData = { option_ids: checked };

    } else if (method === 'borda' || method === 'irv' || method === 'condorcet') {
      const items = document.querySelectorAll('#rankList .rank-item');
      const order = Array.from(items).map(item => parseInt(item.dataset.id));
      // borda は rankings フォーマット、irv/condorcet は order フォーマット
      if (method === 'borda') {
        const rankings = {};
        order.forEach((id, idx) => { rankings[id] = idx + 1; });
        voteData = { rankings };
      } else {
        voteData = { order };
      }

    } else if (method === 'score') {
      const sliders = document.querySelectorAll('.score-slider');
      const scores = {};
      sliders.forEach(s => { scores[s.dataset.id] = parseInt(s.value); });
      voteData = { scores };

    } else if (method === 'majority_judgement') {
      const grades = {};
      let allGraded = true;
      document.querySelectorAll('.mj-grade-group').forEach(group => {
        const optId = group.dataset.id;
        const activeBtn = group.querySelector('.mj-btn.active-grade');
        if (!activeBtn) { allGraded = false; }
        else { grades[optId] = activeBtn.dataset.grade; }
      });
      if (!allGraded) {
        alert('すべての選択肢を評価してください。');
        return false;
      }
      voteData = { grades };

    } else if (method === 'quadratic') {
      // qvVotes はテンプレート内で定義済み
      if (typeof qvVotes === 'undefined') { alert('投票データエラー'); return false; }
      const allZero = Object.values(qvVotes).every(v => v === 0);
      if (allZero) { alert('少なくとも1つの選択肢に票を配分してください。'); return false; }
      voteData = { votes: qvVotes };

    } else if (method === 'negative') {
      const votes = {};
      const groups = document.querySelectorAll('.btn-group[data-id]');
      groups.forEach(group => {
        const optId = group.dataset.id;
        const activeBtn = group.querySelector('.negative-btn.active-positive, .negative-btn.active-neutral, .negative-btn.active-negative');
        if (activeBtn) {
          votes[optId] = parseInt(activeBtn.dataset.val);
        } else {
          votes[optId] = 0;
        }
      });
      voteData = { votes };
    }

    if (!voteData) { alert('投票データを作成できませんでした。'); return false; }

    document.getElementById('voteDataInput').value = JSON.stringify(voteData);
    return true;

  } catch (e) {
    console.error('Vote preparation error:', e);
    alert('投票データの作成中にエラーが発生しました。');
    return false;
  }
}

// ===== ページ初期化 =====
document.addEventListener('DOMContentLoaded', function () {
  // 負の投票: デフォルトで「棄権」をアクティブに
  document.querySelectorAll('.negative-btn[data-val="0"]').forEach(btn => {
    btn.classList.add('active-neutral');
  });
});
