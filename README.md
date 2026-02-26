# Majority-Judgement
マジョリティ・ジャッジメント（MJ）方式を採用した、より民主的で正確な意思決定を支援する投票プラットフォームです。

# 🌟 プロジェクト概要
従来の多数決（単記非移譲式）では、「死票」が多くなりがちで、中庸な意見が無視される傾向があります。本システムでは、各選択肢に対して「評価（Grade）」を付与し、その**中央値（Median）**に基づいて順位を決定することで、集団の納得感が最も高い結果を導き出します。
# 🛠 技術スタック
| レイヤー | 技術 |
|---|---|
| Frontend | React (Vite / TypeScript / Tailwind CSS) |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Auth | JWT (python-jose) |
| Infrastructure | GCP (Cloud Run / Cloud SQL) |
| IaC / CI/CD | Terraform / GitHub Actions |
| Proxy / Server | Nginx / Docker & Docker Compose |
# 📋 機能一覧
 * 投票フォーム作成: 選択肢の追加、評価スケール（例：最高〜不適切）のカスタマイズ。
 * 投票ページ: 各選択肢に対する多段階評価入力インターフェース。
 * 結果確認ページ: 各評価の割合を可視化する積み上げ棒グラフ表示。
 * 順位計算アルゴリズム: MJ特有の中央値比較とタイブレーク処理。
 * 順位確認ページ: 最終的なランキングと計算プロセスの提示。
# 🧮 順位計算ロジック (Majority Judgment)
本システムでは、以下のアルゴリズムに基づいて順位を決定します。
1. 中央値の選定
各候補 C に対する n 個の評価を g_1 \leq g_2 \leq \dots \leq g_n と並べたとき、中央値 M を算出します。
 * n が奇数の場合: M = g_{(n+1)/2}
 * n が偶数の場合: M = g_{n/2} （低い方の中央値を採用）
2. タイブレーク（順次除去法）
中央値 M が同一の候補が複数存在する場合、以下の手順を繰り返します：
 * 各候補から中央値 M と一致する評価を1つ取り除く。
 * 残った評価群から新しい中央値を算出し、比較する。
 * 差が出るまで、または評価がなくなるまで継続。
# 🏗 システム構成
データベース・スキーマ
erDiagram
    Users ||--o{ Polls : creates
    Polls ||--o{ Options : contains
    Options ||--o{ Votes : receives
    Grades ||--o{ Votes : defines
    Users ||--o{ Votes : casts

API エンドポイント (主要なもの)
 * POST /api/v1/polls: 新規投票作成
 * GET /api/v1/polls/{id}: 投票フォーム取得
 * POST /api/v1/polls/{id}/vote: 投票実行
 * GET /api/v1/polls/{id}/results: 集計・順位結果取得
🚀 セットアップ (ローカル開発環境)
# リポジトリのクローン
git clone https://github.com/username/mj-voting-app.git

# Docker Composeによる起動
docker-compose up --build

起動後、フロントエンドは http://localhost:3000、APIドキュメントは http://localhost:8000/docs で確認できます。
# 🌐 デプロイ
Terraformを使用してGCP上に構築します。
 * terraform/ ディレクトリで terraform apply を実行。
 * GitHub Actionsにより、mainブランチへのPushでCloud Runへ自動デプロイ。
いかがでしょうか？プロジェクトの「顔」として十分な情報を詰め込んでおきました。
次は、**このREADMEに記載したデータベース構成を実現するためのSQLAlchemyモデル定義（Pythonコード）**を作成しますか？それとも、計算ロジックのユニットテスト案を考えましょうか？
