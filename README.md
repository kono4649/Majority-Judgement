# 投票アプリ

9種類の投票方式に対応した多機能Webアプリケーションです。

## 機能

- **ユーザー登録・認証** — メールアドレスとパスワードで登録。メールアクティベーション付き
- **投票フォーム作成** — 9種類の投票方式から選択。有効期間（日時）を設定・変更可能
- **匿名投票** — 投票URLを知っていれば誰でも匿名で投票可能
- **重複投票防止** — Cookieによる指紋でフォームごとに1票を保証
- **結果閲覧・CSV出力** — 作成者のみ結果の閲覧とCSVダウンロードが可能

## 対応投票方式

| 方式 | 説明 |
|------|------|
| 単記投票（多数決） | 1つだけ選ぶ。最多票の選択肢が勝者 |
| 承認投票 | 許容できるものすべてに投票。承認数最多が勝者 |
| ボルダ・カウント | 全選択肢に順位付け。1位=n-1点、2位=n-2点…の合計で比較 |
| 代替投票（IRV） | 優先順位付き。過半数なければ最下位を除外して再集計 |
| コンドルセ方式 | 順位から一対比較を導出。全対戦に勝つ選択肢が勝者 |
| スコア投票 | 各選択肢に数値スコアを付与。平均スコアで比較 |
| マジョリティ・ジャッジメント | 6段階評価（優秀〜拒否）の中央値で順位付け |
| クアドラティック・ボーティング | クレジット予算内で票を配分。コスト=票数²で支持強度を表現 |
| 負の投票 | 各選択肢に賛成(+1)・棄権(0)・反対(-1)を投じる |

## 技術スタック

- **バックエンド**: Python / FastAPI
- **データベース**: SQLite（SQLAlchemy ORM）
- **テンプレート**: Jinja2
- **フロントエンド**: Bootstrap 5 / SortableJS（ドラッグ&ドロップ順位付け） / Chart.js（結果グラフ）
- **認証**: JWT（httponly Cookie）/ bcrypt

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集してください。

```ini
# 必須: ランダムな秘密鍵を設定
SECRET_KEY=your-random-secret-key-here

# アプリのベースURL（投票URLの生成に使用）
BASE_URL=http://localhost:8000

# 開発モード: True の場合、メールを送らずアクティベーションURLをコンソールに表示
DEV_MODE=True

# メール送信が必要な場合はSMTP設定を入力
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@example.com
```

### 3. 起動

```bash
python run.py
```

ブラウザで `http://localhost:8000` を開いてください。

## 使い方

### 投票フォームを作る（登録が必要）

1. `/auth/register` でアカウント登録
2. アクティベーションメール（開発モードはコンソール表示）のURLをクリック
3. `/auth/login` でログイン
4. ダッシュボードから「新規投票作成」
5. タイトル・投票方式・選択肢・有効期間を入力して作成

### 投票する（登録不要・匿名）

1. 作成者から投票URLを受け取る（例: `http://localhost:8000/vote/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）
2. URLにアクセスして投票
3. 同じブラウザからの2回目の投票は拒否されます

### 結果を見る（作成者のみ）

- ダッシュボードの「結果」ボタン → グラフ＋テーブルで表示
- 「CSV ダウンロード」ボタン → 全票データをCSV出力

## パスワード要件

- 8文字以上
- 大文字・小文字・数字・記号（`!@#$%^&*`など）をそれぞれ1文字以上含む

## 重複投票防止の仕組み

- 初回訪問時にブラウザへランダムなIDをhttponly Cookieとして付与
- 投票時に `HMAC(voter_id + poll_id)` をフィンガープリントとしてDBに保存
- 同一ブラウザからの2票目は拒否
- Cookieを削除すると再投票が可能になる点は既知の制限です

## ファイル構成

```
├── app/
│   ├── main.py          # FastAPIアプリ本体
│   ├── config.py        # 設定・定数
│   ├── database.py      # SQLAlchemy設定
│   ├── models.py        # DBモデル（User, Poll, PollOption, Vote）
│   ├── auth.py          # JWT・パスワードユーティリティ
│   ├── email_utils.py   # メール送信
│   ├── voting.py        # 9種類の投票計算エンジン
│   └── routers/
│       ├── auth.py      # 認証ルート
│       ├── polls.py     # 投票フォームCRUD・結果・CSV
│       └── votes.py     # 匿名投票
├── templates/           # Jinja2 HTMLテンプレート
├── static/              # CSS・JavaScript
├── requirements.txt
├── run.py               # 起動スクリプト
└── .env.example         # 環境変数テンプレート
```
