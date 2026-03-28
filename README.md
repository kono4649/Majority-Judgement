# 投票アプリ

9種類の投票方式に対応した多機能Webアプリケーションです。

## 機能

- **ユーザー登録・認証** — メールアドレスとパスワードで登録。メールアクティベーション付き
- **投票フォーム作成** — 9種類の投票方式から選択。有効期間（日時）を設定・変更可能
- **匿名投票** — 投票URLを知っていれば誰でも匿名で投票可能
- **重複投票防止** — Cookie指紋でフォームごとに1票を保証
- **結果閲覧・CSV出力** — 作成者のみ結果の閲覧とCSVダウンロードが可能

## 対応投票方式

| 方式 | 説明 |
|------|------|
| 単記投票（多数決） | 1つだけ選ぶ。最多票の選択肢が勝者 |
| 承認投票 | 許容できるものすべてに投票。承認数最多が勝者 |
| ボルダ・カウント | ドラッグ&ドロップで順位付け。1位=n-1点…の合計ポイントで比較 |
| 代替投票（IRV） | 優先順位付き。過半数なければ最下位を除外して再集計 |
| コンドルセ方式 | 順位から一対比較を導出。全対戦に勝つ選択肢が勝者 |
| スコア投票 | 各選択肢にスコアを付与。平均スコアで比較 |
| マジョリティ・ジャッジメント | 6段階評価（優秀〜拒否）の中央値で順位付け |
| クアドラティック・ボーティング | クレジット予算内で票を配分。コスト=票数²で支持強度を表現 |
| 負の投票 | 各選択肢に賛成(+1)・棄権・反対(-1)を投じる |

## 技術スタック

| 区分 | 技術 |
|------|------|
| **フロントエンド** | React 18 / Vite / React Router v6 |
| **UIライブラリ** | カスタムCSS（コンポーネント別ファイル）/ Chart.js / @dnd-kit（ドラッグ&ドロップ） |
| **バックエンド** | Python / FastAPI |
| **データベース** | SQLite（SQLAlchemy ORM） |
| **認証** | JWT（httponly Cookie）/ bcrypt |
| **インフラ** | Docker / Docker Compose / Nginx（リバースプロキシ） |

## ファイル構成

```
├── app/                        # FastAPI バックエンド
│   ├── main.py                 # アプリ本体・CORS設定
│   ├── config.py               # 設定・定数
│   ├── database.py             # SQLAlchemy設定
│   ├── models.py               # DBモデル
│   ├── schemas.py              # Pydanticスキーマ
│   ├── auth.py                 # JWT・パスワードユーティリティ
│   ├── email_utils.py          # メール送信
│   ├── voting.py               # 9種類の投票計算エンジン
│   └── routers/
│       ├── auth.py             # 認証API (/api/auth/...)
│       ├── polls.py            # 投票フォームCRUD・結果・CSV API
│       └── votes.py            # 匿名投票API
│
├── frontend/                   # React フロントエンド
│   ├── src/
│   │   ├── api/client.js       # APIクライアント（fetchラッパー）
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx # 認証状態管理
│   │   ├── components/
│   │   │   ├── Navbar/
│   │   │   │   ├── Navbar.jsx
│   │   │   │   └── Navbar.css
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── voting/         # 投票入力コンポーネント（各JSX+CSS）
│   │   │       ├── PluralityVote.jsx / .css
│   │   │       ├── ApprovalVote.jsx / .css
│   │   │       ├── RankingVote.jsx / .css   # Borda・IRV・Condorcet共用
│   │   │       ├── ScoreVote.jsx / .css
│   │   │       ├── MajorityJudgementVote.jsx / .css
│   │   │       ├── QuadraticVote.jsx / .css
│   │   │       └── NegativeVote.jsx / .css
│   │   └── pages/              # ページコンポーネント（各JSX+CSS）
│   │       ├── Home/           Dashboard/ CreatePoll/ EditPoll/
│   │       ├── Login/          Register/ VotePage/ ThanksPage/ Results/
│   ├── nginx.conf              # Nginx設定（SPA・APIプロキシ）
│   └── Dockerfile
│
├── Dockerfile                  # バックエンド用
├── docker-compose.yml
├── requirements.txt
├── run.py                      # 開発用起動スクリプト
└── .env.example
```

## Docker での起動（推奨）

```bash
# 1. リポジトリをクローン
git clone <repo-url>
cd Majority-Judgement

# 2. 環境変数ファイルを作成（任意）
cp .env.example .env
# .env を編集して SECRET_KEY などを設定

# 3. 起動
docker compose up --build

# ブラウザで http://localhost を開く
```

> `docker compose up` 後、バックエンドのヘルスチェックが通過してからフロントエンドが起動します。

## ローカル開発環境

### バックエンド

```bash
pip install -r requirements.txt
cp .env.example .env
python run.py
# → http://localhost:8000 で API サーバー起動
```

### フロントエンド

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173 で開発サーバー起動
```

> Vite の開発サーバーは `/api` リクエストを `http://localhost:8000` にプロキシします。

## 環境変数（`.env`）

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `SECRET_KEY` | *(要変更)* | JWT署名用の秘密鍵 |
| `BASE_URL` | `http://localhost:8000` | APIのベースURL（メール内のアクティベーションURL生成に使用） |
| `FRONTEND_URL` | `http://localhost:5173` | フロントエンドのURL（アクティベーション後のリダイレクト先） |
| `CORS_ORIGINS` | `http://localhost:5173,...` | 許可するCORSオリジン（カンマ区切り） |
| `DEV_MODE` | `true` | `true` にするとメール送信の代わりにコンソールにURLを表示 |
| `DATABASE_URL` | `sqlite:///./voting_app.db` | データベースURL |
| `SMTP_HOST` | *(空)* | SMTPサーバー（空の場合はDEV_MODEとして動作） |

## 使い方

### 投票フォームを作成する（登録が必要）

1. `http://localhost/register` でアカウント登録
2. アクティベーションメール（DEV_MODEではコンソール表示）のURLをクリック
3. `http://localhost/login` でログイン
4. ダッシュボードから「新規作成」
5. タイトル・投票方式・選択肢・有効期間を入力して作成

### 投票する（登録不要・匿名）

1. 作成者から投票URLを受け取る（例: `http://localhost/vote/xxxx-xxxx-xxxx`）
2. URLにアクセスして投票
3. 同じブラウザからの2回目の投票は拒否されます

### 結果を見る（作成者のみ）

- ダッシュボードの「📊 結果」ボタン → グラフ＋テーブルで表示
- 「⬇️ CSV」ボタン → 全票データをCSV出力

## パスワード要件

- 8文字以上
- 大文字・小文字・数字・記号（`!@#$%^&*`など）をそれぞれ1文字以上含む

## 重複投票防止の仕組み

- 初回訪問時にブラウザへランダムなIDをhttponly Cookieとして付与
- 投票時に `HMAC(voter_id + poll_id)` をフィンガープリントとしてDBに保存
- 同一ブラウザからの2票目は拒否
- Cookieを削除すると再投票が可能になる点は既知の制限です

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| `POST` | `/api/auth/register` | ユーザー登録 |
| `GET`  | `/api/auth/activate/{token}` | メールアクティベーション |
| `POST` | `/api/auth/login` | ログイン（Cookieセット） |
| `POST` | `/api/auth/logout` | ログアウト |
| `GET`  | `/api/auth/me` | 現在のユーザー情報 |
| `GET`  | `/api/polls/` | 投票フォーム一覧 |
| `POST` | `/api/polls/` | 投票フォーム作成 |
| `PUT`  | `/api/polls/{id}` | 投票フォーム更新 |
| `DELETE` | `/api/polls/{id}` | 投票フォーム削除 |
| `GET`  | `/api/polls/{id}/results` | 集計結果 |
| `GET`  | `/api/polls/{id}/results/csv` | CSV ダウンロード |
| `GET`  | `/api/vote/{public_id}` | 投票フォーム取得（公開） |
| `GET`  | `/api/vote/{public_id}/status` | 投票済みチェック |
| `POST` | `/api/vote/{public_id}` | 投票送信 |
