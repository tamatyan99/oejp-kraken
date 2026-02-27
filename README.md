# OEJP Kraken Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Octopus Energy Japan（OEJP）Kraken APIと連携するHome Assistantカスタムインテグレーションです。

## 機能

### センサー

| センサー名 | 説明 | 単位 | Energy Dashboard対応 |
|-----------|------|------|---------------------|
| `sensor.oejp_current_power` | 現在の消費電力 | W | ❌ |
| `sensor.oejp_today_consumption` | 本日の消費量 | kWh | ✅ |
| `sensor.oejp_current_rate` | 現在の電気料金単価 | JPY/kWh | ❌ |

### 主な機能

- 📊 **リアルタイム電力監視**: 現在の消費電力をワット単位で表示
- 📈 **エネルギー使用量追跡**: 本日の消費量をkWhで追跡（Energy Dashboard対応）
- 💰 **電気料金確認**: 現在の料金単価を円/kWhで表示
- 🔄 **自動更新**: 5-15分間隔で自動更新（設定可能）
- 🔐 **安全な認証**: トークンベース認証（自動リフレッシュ対応）

## インストール

### HACS経由（推奨）

1. HACSをインストール（未インストールの場合）
2. HACS → 「カスタムリポジトリの追加」
3. リポジトリURL: `https://github.com/your-username/oejp-kraken`
4. カテゴリ: 「インテグレーション」
5. 「OEJP Kraken」をインストール
6. Home Assistantを再起動

### 手動インストール

1. 最新のリリースをダウンロード
2. `custom_components/oejp_kraken/`フォルダを作成
3. ダウンロードしたファイルをコピー
4. Home Assistantを再起動

## 設定

### UI設定フロー

1. **設定** → **デバイスとサービス** → **統合を追加**
2. 「OEJP Kraken」を検索して選択
3. 以下の情報を入力:
   - **メールアドレス**: OEJPアカウントのメールアドレス
   - **パスワード**: OEJPアカウントのパスワード
   - **更新間隔**: データ更新間隔（秒、60-3600秒、デフォルト300秒）
4. 「送信」をクリック

### オプション設定

設定後、統合カードから「オプション」をクリックして:
- 更新間隔の変更

## Energy Dashboard統合

`sensor.oejp_today_consumption`はEnergy Dashboardと連携できます:

1. **設定** → **ダッシュボード** → **エネルギー**
2. 「グリッド消費量」→「追加」
3. `sensor.oejp_today_consumption`を選択

## トラブルシューティング

### 認証エラー

- メールアドレスとパスワードを確認
- OEJPアカウントが有効であることを確認

### データが更新されない

- ログを確認: **設定** → **システム** → **ログ**
- APIレート制限に達していないか確認

### センサーが表示されない

- 統合が正常にセットアップされているか確認
- Home Assistantを再起動

## 必要条件

- Home Assistant 2023.7.0以上
- Python 3.11以上
- aiohttp 3.8.0以上

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## サポート

問題がある場合は、GitHub Issuesで報告してください。

## 謝辞

- Octopus Energy Japan
- Home Assistant Community
- BottlecapDave's Octopus Energy integration (パターン参考)
