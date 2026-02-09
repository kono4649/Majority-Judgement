// Majority Judgement - アプリケーションロジック

const GRADES = [
  { key: "excellent", label: "非常に良い", css: "excellent" },
  { key: "verygood", label: "良い", css: "verygood" },
  { key: "good", label: "やや良い", css: "good" },
  { key: "acceptable", label: "普通", css: "acceptable" },
  { key: "poor", label: "やや悪い", css: "poor" },
  { key: "reject", label: "不可", css: "reject" },
];

let state = {
  question: "",
  candidates: [],
  voterCount: 0,
  currentVoter: 0,
  votes: [], // votes[candidateIndex][gradeIndex] = count
};

// --- 設定セクション ---

function addCandidate() {
  const list = document.getElementById("candidates-list");
  const div = document.createElement("div");
  div.className = "candidate-input";
  div.innerHTML =
    '<input type="text" class="candidate" placeholder="候補者名">' +
    '<button class="btn-remove" onclick="removeCandidate(this)" title="削除">&times;</button>';
  list.appendChild(div);
}

function removeCandidate(btn) {
  const list = document.getElementById("candidates-list");
  if (list.children.length > 2) {
    btn.parentElement.remove();
  }
}

function startVoting() {
  const question = document.getElementById("question").value.trim();
  if (!question) {
    alert("質問・議題を入力してください。");
    return;
  }

  const candidateInputs = document.querySelectorAll(".candidate");
  const candidates = [];
  candidateInputs.forEach(function (input) {
    const val = input.value.trim();
    if (val) candidates.push(val);
  });

  if (candidates.length < 2) {
    alert("候補者を2名以上入力してください。");
    return;
  }

  const voterCount = parseInt(document.getElementById("voter-count").value, 10);
  if (!voterCount || voterCount < 1) {
    alert("投票者数を1以上で入力してください。");
    return;
  }

  state.question = question;
  state.candidates = candidates;
  state.voterCount = voterCount;
  state.currentVoter = 1;
  state.votes = candidates.map(function () {
    return GRADES.map(function () {
      return 0;
    });
  });

  document.getElementById("setup-section").classList.add("hidden");
  showVotingForm();
}

// --- 投票セクション ---

function showVotingForm() {
  var section = document.getElementById("voting-section");
  section.classList.remove("hidden");

  document.getElementById("voting-title").textContent = state.question;
  document.getElementById("voter-label").textContent =
    "投票者 " + state.currentVoter + " / " + state.voterCount;

  var formHtml = "";
  state.candidates.forEach(function (candidate, ci) {
    formHtml += '<div class="voting-candidate">';
    formHtml += '<div class="candidate-name">' + escapeHtml(candidate) + "</div>";
    formHtml += '<div class="grade-options">';
    GRADES.forEach(function (grade, gi) {
      var id = "c" + ci + "g" + gi;
      formHtml += "<label>";
      formHtml +=
        '<input type="radio" name="candidate' + ci + '" value="' + gi + '" id="' + id + '">';
      formHtml +=
        '<span class="grade-label grade-' +
        grade.css +
        '" onclick="activateGrade(this, \'' +
        grade.css +
        "')" >" +
        escapeHtml(grade.label) +
        "</span>";
      formHtml += "</label>";
    });
    formHtml += "</div></div>";
  });

  document.getElementById("voting-form").innerHTML = formHtml;
}

function activateGrade(span, gradeCss) {
  var container = span.closest(".grade-options");
  container.querySelectorAll(".grade-label").forEach(function (el) {
    // Remove all active classes
    GRADES.forEach(function (g) {
      el.classList.remove("grade-" + g.css + "-active");
    });
  });
  span.classList.add("grade-" + gradeCss + "-active");
}

function submitVote() {
  for (var ci = 0; ci < state.candidates.length; ci++) {
    var selected = document.querySelector('input[name="candidate' + ci + '"]:checked');
    if (!selected) {
      alert(state.candidates[ci] + " の評価を選択してください。");
      return;
    }
    var gi = parseInt(selected.value, 10);
    state.votes[ci][gi]++;
  }

  state.currentVoter++;

  if (state.currentVoter > state.voterCount) {
    document.getElementById("voting-section").classList.add("hidden");
    showResults();
  } else {
    showVotingForm();
  }
}

// --- 結果セクション ---

function showResults() {
  var section = document.getElementById("result-section");
  section.classList.remove("hidden");

  document.getElementById("result-question").textContent = state.question;

  // Build result table
  var html = '<table class="result-table"><thead><tr><th>候補者</th>';
  GRADES.forEach(function (g) {
    html += "<th>" + escapeHtml(g.label) + "</th>";
  });
  html += "<th>中央値</th></tr></thead><tbody>";

  var results = state.candidates.map(function (candidate, ci) {
    var median = computeMedianGrade(state.votes[ci]);
    return { name: candidate, index: ci, medianIndex: median };
  });

  // Sort by median grade (lower index = better)
  results.sort(function (a, b) {
    if (a.medianIndex !== b.medianIndex) return a.medianIndex - b.medianIndex;
    // Tie-break: compare proponents and opponents
    return tieBreak(a.index, b.index);
  });

  var winnerIndex = results[0].index;

  results.forEach(function (r) {
    var isWinner = r.index === winnerIndex;
    html += '<tr class="' + (isWinner ? "winner-row" : "") + '">';
    html += "<td>" + escapeHtml(r.name) + "</td>";
    state.votes[r.index].forEach(function (count) {
      html += "<td>" + count + "</td>";
    });
    html += "<td>" + escapeHtml(GRADES[r.medianIndex].label) + "</td>";
    html += "</tr>";
  });

  html += "</tbody></table>";
  document.getElementById("result-table-container").innerHTML = html;

  // Winner announcement
  var winner = results[0];
  document.getElementById("winner-announcement").innerHTML =
    '<div class="winner-title">最優秀評価</div>' +
    '<div class="winner-name">' +
    escapeHtml(winner.name) +
    "</div>" +
    '<div class="winner-grade">中央値: ' +
    escapeHtml(GRADES[winner.medianIndex].label) +
    "</div>";
}

function computeMedianGrade(gradeCounts) {
  var total = gradeCounts.reduce(function (s, v) {
    return s + v;
  }, 0);
  var half = Math.floor(total / 2);
  var cumulative = 0;

  for (var i = 0; i < gradeCounts.length; i++) {
    cumulative += gradeCounts[i];
    if (cumulative > half) return i;
  }
  return gradeCounts.length - 1;
}

function tieBreak(indexA, indexB) {
  // Compare by removing median voters one at a time
  var votesA = state.votes[indexA].slice();
  var votesB = state.votes[indexB].slice();

  var medianA = computeMedianGrade(votesA);
  var medianB = computeMedianGrade(votesB);

  if (medianA !== medianB) return medianA - medianB;

  // Count proponents (better than median) and opponents (worse than median)
  var proA = 0,
    oppA = 0;
  for (var i = 0; i < medianA; i++) proA += votesA[i];
  for (var i = medianA + 1; i < votesA.length; i++) oppA += votesA[i];

  var proB = 0,
    oppB = 0;
  for (var i = 0; i < medianB; i++) proB += votesB[i];
  for (var i = medianB + 1; i < votesB.length; i++) oppB += votesB[i];

  // Higher proportion of proponents wins
  var totalA = votesA.reduce(function (s, v) {
    return s + v;
  }, 0);
  var totalB = votesB.reduce(function (s, v) {
    return s + v;
  }, 0);

  var proRatioA = totalA > 0 ? proA / totalA : 0;
  var proRatioB = totalB > 0 ? proB / totalB : 0;

  if (proRatioA !== proRatioB) return proRatioB - proRatioA > 0 ? 1 : -1;

  return 0;
}

// --- リセット ---

function resetAll() {
  state = {
    question: "",
    candidates: [],
    voterCount: 0,
    currentVoter: 0,
    votes: [],
  };

  document.getElementById("result-section").classList.add("hidden");
  document.getElementById("voting-section").classList.add("hidden");

  document.getElementById("question").value = "";
  document.getElementById("voter-count").value = "5";
  document.getElementById("candidates-list").innerHTML =
    '<div class="candidate-input">' +
    '<input type="text" class="candidate" placeholder="候補者名">' +
    '<button class="btn-remove" onclick="removeCandidate(this)" title="削除">&times;</button>' +
    "</div>" +
    '<div class="candidate-input">' +
    '<input type="text" class="candidate" placeholder="候補者名">' +
    '<button class="btn-remove" onclick="removeCandidate(this)" title="削除">&times;</button>' +
    "</div>";

  document.getElementById("setup-section").classList.remove("hidden");
}

// --- ユーティリティ ---

function escapeHtml(str) {
  var div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}
