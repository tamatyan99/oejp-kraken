# AGENTS.md

エージェント管理用ファイル

## セッション記録

作業の履歴追跡と再開のためにセッション情報を記録します。

### アクティブセッション

| セッションID | 開始日時 | ステータス | 説明 |
|-----------|---------|---------|------|
| ses_365411ff6ffeOfbtJC9vsWdxpc | 2026-02-26T16:19:04Z | 完了 | OEJP Kraken API分析・インテグレーション計画作成 |
| ses_365411ff6ffeOfbtJC9vsWdxpc | 2026-02-26T16:59:28Z | 完了 | インテグレーション実装（Wave 1-4完了） |
| ses_365411ff6ffeOfbtJC9vsWdxpc | 2026-02-27T06:19:19Z | アクティブ | AGENTS.md作成・セッション継続設定 |

### セッション履歴

| セッションID | プロジェクト | 開始日時 | 完了日時 | メモ |
|-----------|---------|---------|---------|-----|
| ses_365411ff6ffeOfbtJC9vsWdxpc | OEJP Kraken Integration | 2026-02-26T16:19:04Z | 2026-02-27T06:19:19Z | MVP実装完了（3センサー） |

---

## エージェント情報

### 使用可能なエージェント

| エージェント名 | カテゴリ | 用途 |
|-----------|---------|------|
| Sisyphus | オーケストレーター | 全体統括・調整 |
| Prometheus | プランビルダー | 作業計画作成 |
| Atlas | プラン実行者 | 作業計画実行 |
| Metis | 事前コンサルタント | 要件分析・ギャップ特定 |
| Momus | レビューアー | 作業計画の品質レビュー |
| Oracle | リードオンリーコンサルタント | アーキテクチャ・複雑問題の解決 |
| Librarian | 外部リファレンスエージェント | ドキュメント検索・外部コード例検索 |

### エージェント起動条件

- **Sisyphus**: 全ての作業
- **Prometheus**: ユーザーからの具体的なリクエスト
- **Atlas**: プランが作成された後の実行
- **Metis**: 複雑・不明確なタスクの要件分析
- **Momus**: 作業計画の品質チェック
- **Oracle**: アーキテクチャ決定、複雑問題の解決
- **Librarian**: 外部ライブラリ・ドキュメントの調査

---

## GitHub 認証設定

### リポジトリ情報

- **リポジトリ名**: oejp-kraken
- **所有者**: tamatyan99
- **ブランチ**: main
- **リモートURL**: https://github.com/tamatyan99/oejp-kraken.git

### Git 設定

```bash
# リモートリポジトリの設定（既に設定済み）
git remote add origin https://github.com/tamatyan99/oejp-kraken.git

# ブランチの確認
git branch -M main

# ユーザー名とメールの設定
git config user.name "Your Name"
git config user.email "your.email@example.com"

# GPG署名の設定（推奨）
git config commit.gpgsign true
```

### 別セッションでのプッシュ手順

```bash
# 1. 作業ディレクトリへ移動
cd /root/HomeAssistant

# 2. 変更を確認
git status

# 3. 変更をステージング
git add .

# 4. コミット
git commit -m "feat: 変更内容の説明"

# 5. プッシュ
git push origin main
```

---

## 作業進捗状況

### 現在のプロジェクト

**プロジェクト名**: OEJP Kraken Home Assistant Integration
**ステータス**: MVP実装完了（テスト待ち）
**最終更新**: 2026-02-27

### 完了したタスク

- [x] Wave 1: API調査・検証
- [x] Wave 1: HAエネルギー統合パターン調査
- [x] Wave 1: 基本ファイル構造作成
- [x] Wave 2: GraphQLクライアント実装
- [x] Wave 2: DataUpdateCoordinator実装
- [x] Wave 3: MVPセンサー実装（3センサー）
- [x] Wave 3: 設定フロー・翻訳ファイル実装
- [x] Wave 4: HACS対応・ドキュメント作成
- [x] Wave 4: 統合テスト・検証

### 残タスク

- [ ] ドラフト削除 - /start-workガイダンス
- [ ] 実際のテスト実行（Home Assistant環境での動作確認）

### 作成されたファイル

```
custom_components/oejp_kraken/
├── __init__.py
├── config_flow.py
├── const.py
├── coordinator.py
├── graphql_client.py
├── manifest.json
├── sensor.py
└── translations/
    └── ja.json
```

---

## トークン管理情報

### 保存場所

**Home Assistant Config Entry Storage**:
`~/.homeassistant/.storage/config_entries.json`

**注意**: トークンはHome Assistantが自動的に暗号化して保存します。手動で編集しないでください。

### トークンライフサイクル

- **アクセストークン**: 60分有効
- **リフレッシュトークン**: 7日有効
- **自動リフレッシュ**: coordinator.pyで実装済み

---

## セッション管理ガイド

### 新規セッションの開始

1. このファイルの「アクティブセッション」にセッションIDを記録
2. 作業内容を随時追跡

### セッションの再開

1. セッションIDを確認
2. 前回の作業状態を確認
3. 必要なコンテキストを保持したまま再開

### セッションの完了

1. セッションIDを「履歴」に移動
2. 成果物を記録

---

## 環境情報

### 必要な環境

- **Home Assistant**: 2023.7.0以上
- **Python**: 3.11以上
- **依存関係**: aiohttp>=3.8.0

### 現在の設定

- **作業ディレクトリ**: `/root/HomeAssistant`
- **リポジトリ**: `oejp-kraken`
- **ブランチ**: `main`
- **リモート**: `origin`（GitHub）

---

## 最終更新

- **作成日**: 2026-02-27
- **作成者**: Sisyphus (オーケストレーター)
- **目的**: セッション管理と GitHub 連携の標準化
- **更新履歴**:
  - 2026-02-27: セッション履歴・GitHub設定・作業進捗を追加

エージェント管理用ファイル

## セッション記録

作業の履歴追跡と再開のためにセッション情報を記録します。

### アクティブセッション

| セッションID | 開始日時 | ステータス | 説明 |
|-----------|---------|---------|------|
| - | - | - |

### セッション履歴

| セッションID | プロジェクト | 開始日時 | 完了日時 | メモ |
|-----------|---------|---------|---------|-----|
| - | - | - | - |

---

## エージェント情報

### 使用可能なエージェント

| エージェント名 | カテゴリ | 用途 |
|-----------|---------|------|
| Sisyphus | オーケストレーター | 全体統括・調整 |
| Prometheus | プランビルダー | 作業計画作成 |
| Atlas | プラン実行者 | 作業計画実行 |
| Metis | 事前コンサルタント | 要件分析・ギャップ特定 |
| Momus | レビューアー | 作業計画の品質レビュー |
| Oracle | リードオンリーコンサルタント | アーキテクチャ・複雑問題の解決 |
| Librarian | 外部リファレンスエージェント | ドキュメント検索・外部コード例検索 |

### エージェント起動条件

- **Sisyphus**: 全ての作業
- **Prometheus**: ユーザーからの具体的なリクエスト
- **Atlas**: プランが作成された後の実行
- **Metis**: 複雑・不明確なタスクの要件分析
- **Momus**: 作業計画の品質チェック
- **Oracle**: アーキテクチャ決定、複雑問題の解決
- **Librarian**: 外部ライブラリ・ドキュメントの調査

---

## GitHub 認証設定

### リポジトリ情報

- **リポジトリ名**: (設定が必要)
- **所有者**: (設定が必要)
- **ブランチ**: `main` (推奨)

### Git 設定

```bash
# リモートリポジトリの設定
git remote add origin https://github.com/username/repo.git

# ブランチの確認
git branch -M main

# ユーザー名とメールの設定
git config user.name "Your Name"
git config user.email "your.email@example.com"

# GPG署名の設定（推奨）
git config commit.gpgsign true
```

---

## セッション管理ガイド

### 新規セッションの開始

1. このファイルの「アクティブセッション」にセッションIDを記録
2. 作業内容を随時追跡

### セッションの再開

1. セッションIDを確認
2. 前回の作業状態を確認
3. 必要なコンテキストを保持したまま再開

### セッションの完了

1. セッションIDを「履歴」に移動
2. 成果物を記録

---

## 最終更新

- **作成日**: 2026-02-27
- **作成者**: Sisyphus (オーケストレーター)
- **目的**: セッション管理と GitHub 連携の標準化
