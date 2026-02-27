# OEJP Kraken Home Assistant Integration

## TL;DR

> **Quick Summary**: OEJP（Octopus Energy Japan）Kraken APIと連携するHome Assistantカスタムインテグレーションを作成。電力使用量、料金情報をリアルタイムで監視。
> 
> **Deliverables**:
> - HACS対応カスタムインテグレーション
> - UI設定フロー（Config Flow）
> - 3つのMVPセンサー（現在電力、本日消費量、現在料金）
> - Energy Dashboard統合対応
> - トークン自動リフレッシュ機能
> 
> **Estimated Effort**: Medium（2-3日）
> **Parallel Execution**: YES - 4 Waves
> **Critical Path**: Task 1 → Task 4 → Task 5 → Task 6 → Task 8

---

## Context

### Original Request
OEJP Kraken API（`https://api.oejp-kraken.energy/v1/graphql/`）を使用したHome Assistantカスタムインテグレーションの作成。電気使用量、料金、請求情報をセンサーとして表示。

### Interview Summary
**Key Discussions**:
- **主機能**: 請求・支払い管理 → 電力使用量監視に変更
- **認証方法**: メールアドレス/パスワード（ObtainKrakenTokenミューテーション）
- **更新頻度**: 5-15分間隔（設定可能）
- **エンティティ**: センサーのみ
- **配布方法**: HACS対応
- **設定方法**: UI設定フロー

**Metis Review Findings**:
- MVPで15センサーはスコープクリープのリスク
- 推奨: 3-5センサーで開始 → ユーザーが3センサーを選択
- GraphQLクエリ最適化が必須
- トークン管理（60分アクセス/7日リフレッシュ）に注意

### Technical Context
- **Home Assistant Version**: 2026.2.3
- **API**: OEJP Kraken GraphQL
- **Authentication**: Token-based（ObtainKrakenToken）
- **Rate Limit**: 50,000ポイント/時間
- **Query Complexity Limit**: 200
- **Node Limit**: 10,000

---

## Work Objectives

### Core Objective
OEJP Kraken APIと連携し、Home Assistantで電力使用量と料金情報をリアルタイム監視するカスタムインテグレーションを構築。

### Concrete Deliverables
1. `custom_components/oejp_kraken/` ディレクトリ構造
2. `manifest.json` - HACS互換
3. `config_flow.py` - UI設定フロー
4. `graphql_client.py` - aiohttpベースGraphQLクライアント
5. `coordinator.py` - DataUpdateCoordinator
6. `sensor.py` - 3つのMVPセンサー
7. `translations/ja.json` - 日本語翻訳
8. `README.md` - インストール・設定ガイド

### Definition of Done
- [ ] HACSからインストール可能
- [ ] UIで設定完了可能
- [ ] 3つのセンサーが正常に動作
- [ ] Energy Dashboardで使用可能
- [ ] トークン自動リフレッシュ動作

### Must Have
- [ ] メール/パスワード認証
- [ ] トークン自動リフレッシュ（60分）
- [ ] 3つのMVPセンサー（current_power, today_consumption, current_rate）
- [ ] Energy Dashboard統合（device_class/state_class正しく設定）
- [ ] 5-15分間隔の更新（設定可能）
- [ ] エラーハンドリング（APIエラー時のgraceful degradation）
- [ ] HACS互換性
- [ ] 日本語UI

### Must NOT Have (Guardrails)
- [ ] 同期的HTTPリクエスト（requestsライブラリ禁止）
- [ ] MVPで15センサー（スコープクリープ防止）
- [ ] ハードコードされたAPIエンドポイント
- [ ] 平文でのトークン保存（暗号化必須）
- [ ] 複数アカウント対応（v2以降）
- [ ] YAML設定（Config Flowのみ）

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO（新規作成）
- **Automated tests**: NO（Home Assistantのテスト基盤は使用しない）
- **Framework**: pytest（オプション、時間があれば）
- **Agent-Executed QA**: 必須

### QA Policy
Every task MUST include agent-executed QA scenarios.

**Verification Methods**:
- **Frontend/UI**: PlaywrightでHome Assistant UIを操作
- **API**: curlでGraphQLエンドポイントをテスト
- **Integration**: 実際のHome Assistantインスタンスで動作確認

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately - Research & Scaffolding):
├── Task 1: OEJP API調査・検証 [deep]
├── Task 2: HAエネルギー統合パターン調査 [deep]
└── Task 3: 基本ファイル構造作成 [quick]

Wave 2 (After Wave 1 - Core Implementation):
├── Task 4: GraphQLクライアント実装 [deep]
└── Task 5: DataUpdateCoordinator実装 [deep]

Wave 3 (After Wave 2 - Sensor & UI):
├── Task 6: MVPセンサー実装 [unspecified-high]
└── Task 7: 設定フロー・翻訳ファイル [quick]

Wave 4 (After Wave 3 - Finalization):
├── Task 8: HACS対応・ドキュメント [writing]
└── Task 9: 統合テスト・検証 [deep]

Wave FINAL (After ALL - Review):
├── Task F1: Plan compliance audit [oracle]
└── Task F2: Code quality review [unspecified-high]

Critical Path: Task 1 → Task 4 → Task 5 → Task 6 → Task 8
Parallel Speedup: ~40% faster than sequential
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | - | 4, 5 |
| 2 | - | 4, 5 |
| 3 | - | 4, 5, 6, 7 |
| 4 | 1, 2, 3 | 5 |
| 5 | 3, 4 | 6 |
| 6 | 3, 5 | 7, 8 |
| 7 | 3, 6 | 8 |
| 8 | 6, 7 | 9 |
| 9 | 8 | F1, F2 |

### Agent Dispatch Summary

- **Wave 1**: 3 tasks → `deep` x2, `quick` x1
- **Wave 2**: 2 tasks → `deep` x2
- **Wave 3**: 2 tasks → `unspecified-high`, `quick`
- **Wave 4**: 2 tasks → `writing`, `deep`
- **FINAL**: 2 tasks → `oracle`, `unspecified-high`

---

## TODOs

- [ ] 1. OEJP API調査・検証

  **What to do**:
  - GraphQLスキーマの確認（Introspectionクエリ）
  - ObtainKrakenTokenミューテーションのテスト
  - 電力使用量・料金取得クエリの確認
  - 実際のクエリコスト測定
  - レート制限の動作確認

  **Must NOT do**:
  - 実装はしない（調査のみ）
  - 実際のユーザー認証情報は使用しない（テストアカウントのみ）

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: APIの詳細調査と検証には深い分析が必要

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 4, Task 5
  - **Blocked By**: None

  **References**:
  - OEJP GraphQL IDE: https://api.oejp-kraken.energy/v1/graphql/
  - OEJP Docs: https://docs.oejp-kraken.energy/graphql/reference/
  - GraphQL Introspection: https://graphql.org/learn/introspection/

  **Acceptance Criteria**:
  - [ ] Introspectionクエリでスキーマ取得成功
  - [ ] ObtainKrakenTokenミューテーションのリクエスト/レスポンス確認
  - [ ] 電力使用量取得クエリの構文確定
  - [ ] クエリコストが200以下であること確認

  **QA Scenarios**:

  ```
  Scenario: GraphQLスキーマ取得
    Tool: Bash (curl)
    Preconditions: なし
    Steps:
      1. curl -X POST https://api.oejp-kraken.energy/v1/graphql/ \
         -H "Content-Type: application/json" \
         -d '{"query": "{ __schema { types { name } } }"}'
    Expected Result: HTTP 200、スキーマ情報が返却
    Evidence: .sisyphus/evidence/task-1-schema.json
  ```

  **Evidence to Capture**:
  - [ ] GraphQLスキーマ（JSON）
  - [ ] 認証フローのレスポンス例
  - [ ] クエリコスト計算結果

  **Commit**: NO

- [ ] 2. Home Assistantエネルギー統合パターン調査

  **What to do**:
  - Home Assistant Coreのoctopus_energy統合を分析
  - DataUpdateCoordinatorの実装パターン調査
  - SensorEntityのdevice_class/state_class設定確認
  - Config Flowの実装パターン調査
  - Energy Dashboard統合のベストプラクティス

  **Must NOT do**:
  - コードのコピー（パターンのみ学習）
  - ライセンス違反となる再利用

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: HAの内部構造とパターン理解が必要

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 4, Task 5
  - **Blocked By**: None

  **References**:
  - HA Core octopus_energy: https://github.com/home-assistant/core/tree/dev/homeassistant/components/octopus_energy
  - HA Integration Docs: https://developers.home-assistant.io/docs/creating_integration_index
  - DataUpdateCoordinator: https://developers.home-assistant.io/docs/integration_fetching_data/

  **Acceptance Criteria**:
  - [ ] octopus_energyのファイル構造を文書化
  - [ ] Coordinatorパターンの実装例を抽出
  - [ ] device_class/state_classの設定パターンを抽出
  - [ ] Config Flowの実装パターンを抽出

  **QA Scenarios**:

  ```
  Scenario: パターン文書化確認
    Tool: Read (file)
    Preconditions: なし
    Steps:
      1. octopus_energy統合のファイル構造を確認
      2. coordinator.pyの実装を分析
      3. sensor.pyのdevice_class設定を確認
    Expected Result: 実装パターンが文書化されている
    Evidence: .sisyphus/evidence/task-2-patterns.md
  ```

  **Evidence to Capture**:
  - [ ] ファイル構造のメモ
  - [ ] コードパターンのスニペット
  - [ ] 実装ガイドライン

  **Commit**: NO

- [ ] 3. 基本ファイル構造作成

  **What to do**:
  - `custom_components/oejp_kraken/` ディレクトリ作成
  - `manifest.json`作成（HACS互換）
  - `const.py`作成（定数定義）
  - `__init__.py`作成（基本構造）
  - `translations/ja.json`作成（日本語翻訳テンプレート）

  **Must NOT do**:
  - 実装ロジックは含めない（スケルトンのみ）
  - ハードコードされた値

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: ファイル作成と基本構造は比較的単純

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 4, Task 5, Task 6, Task 7
  - **Blocked By**: None

  **References**:
  - HA Integration Manifest: https://developers.home-assistant.io/docs/creating_integration_manifest
  - HACS Requirements: https://hacs.xyz/docs/publish/integration

  **Acceptance Criteria**:
  - [ ] ディレクトリ構造が作成される
  - [ ] manifest.jsonに必須フィールドが含まれる
  - [ ] const.pyにドメイン名・デフォルト値が定義される
  - [ ] translations/ja.jsonが作成される

  **QA Scenarios**:

  ```
  Scenario: ファイル構造確認
    Tool: Bash (ls)
    Preconditions: なし
    Steps:
      1. ls -la custom_components/oejp_kraken/
    Expected Result: 必要なファイルが存在
    Evidence: .sisyphus/evidence/task-3-structure.txt
  ```

  **Evidence to Capture**:
  - [ ] ディレクトリ構造のスクリーンショット
  - [ ] manifest.jsonの内容

  **Commit**: YES
  - Message: `feat: initial integration structure`
  - Files: `custom_components/oejp_kraken/*`

- [ ] 4. GraphQLクライアント実装

  **What to do**:
  - `graphql_client.py`作成
  - aiohttpを使用した非同期HTTPクライアント
  - ObtainKrakenTokenミューテーション実装
  - クエリ実行メソッド実装
  - エラーハンドリング（KT-CTエラーコード対応）
  - トークン管理（保存・復号化）

  **Must NOT do**:
  - 同期的なrequestsライブラリ使用
  - 平文でのトークン保存
  - ハードコードされたエンドポイント

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 非同期処理、認証、エラーハンドリングが複雑

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 5
  - **Blocked By**: Task 1, Task 2, Task 3

  **References**:
  - Task 1調査結果（API仕様）
  - Task 2調査結果（パターン）
  - aiohttp Docs: https://docs.aiohttp.org/
  - OEJP Auth Guide: https://docs.oejp-kraken.energy/graphql/guides/basics/

  **Acceptance Criteria**:
  - [ ] authenticate()メソッド実装（トークン取得）
  - [ ] execute_query()メソッド実装
  - [ ] エラーハンドリング（KrakenError例外）
  - [ ] トークンの暗号化保存・復号化
  - [ ] 単体テスト（モック使用）

  **QA Scenarios**:

  ```
  Scenario: 認証フローテスト
    Tool: Bash (curl)
    Preconditions: テスト用認証情報
    Steps:
      1. GraphQLクライアントでauthenticate()呼び出し
      2. トークンが返却されることを確認
      3. トークンが暗号化されて保存されることを確認
    Expected Result: アクセストークンとリフレッシュトークン取得
    Evidence: .sisyphus/evidence/task-4-auth.json
  
  Scenario: クエリ実行テスト
    Tool: Bash (curl)
    Preconditions: 有効なトークン
    Steps:
      1. execute_query()でviewerクエリ実行
      2. レスポンスが正しくパースされることを確認
    Expected Result: クエリ結果が返却
    Evidence: .sisyphus/evidence/task-4-query.json
  ```

  **Evidence to Capture**:
  - [ ] 認証レスポンス例
  - [ ] クエリ実行結果例
  - [ ] エラーハンドリング動作

  **Commit**: YES
  - Message: `feat: add graphql client with auth`
  - Files: `custom_components/oejp_kraken/graphql_client.py`

- [ ] 5. DataUpdateCoordinator実装

  **What to do**:
  - `coordinator.py`作成
  - DataUpdateCoordinator継承クラス実装
  - 定期更新ロジック（5-15分間隔）
  - トークンリフレッシュ統合（60分期限対応）
  - レート制限対応（ポイント計算・制限チェック）
  - エラー時のバックオフ戦略

  **Must NOT do**:
  - トークンリフレッシュの漏れ
  - レート制限無視
  - 例外を握り潰す

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 状態管理、スケジューリング、エラーリカバリが複雑

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 3, Task 4

  **References**:
  - Task 2調査結果（Coordinatorパターン）
  - HA Coordinator Docs: https://developers.home-assistant.io/docs/integration_fetching_data/
  - OEJP Rate Limiting: https://docs.oejp-kraken.energy/graphql/guides/basics/

  **Acceptance Criteria**:
  - [ ] OEJPDataUpdateCoordinatorクラス実装
  - [ ] _async_update_data()メソッド実装
  - [ ] トークンリフレッシュロジック（60分チェック）
  - [ ] レート制限チェック（rateLimitInfoクエリ使用）
  - [ ] update_interval設定（5-15分、設定可能）

  **QA Scenarios**:

  ```
  Scenario: データ更新テスト
    Tool: Bash (python)
    Preconditions: 有効な設定エントリ
    Steps:
      1. Coordinator初期化
      2. async_config_entry_first_refresh()呼び出し
      3. データが正しく取得されることを確認
    Expected Result: センサーデータが更新される
    Evidence: .sisyphus/evidence/task-5-coordinator.log
  
  Scenario: トークンリフレッシュテスト
    Tool: Bash (python)
    Preconditions: 期限切れ間近のトークン
    Steps:
      1. 期限切れトークンでCoordinator初期化
      2. データ更新をトリガー
      3. 自動的にリフレッシュされることを確認
    Expected Result: 新しいトークンで更新成功
    Evidence: .sisyphus/evidence/task-5-refresh.log
  ```

  **Evidence to Capture**:
  - [ ] データ更新ログ
  - [ ] トークンリフレッシュ動作
  - [ ] レート制限レスポンス

  **Commit**: YES
  - Message: `feat: add data update coordinator`
  - Files: `custom_components/oejp_kraken/coordinator.py`

- [ ] 6. MVPセンサー実装

  **What to do**:
  - `sensor.py`作成
  - 3つのセンサークラス実装:
    1. OEJPCurrentPowerSensor（現在の消費電力、W）
    2. OEJPTodayConsumptionSensor（本日の消費量、kWh）
    3. OEJPCurrentRateSensor（現在の料金単価、円/kWh）
  - device_class/state_class正しく設定
  - Energy Dashboard統合対応
  - アイコン・単位・名前の設定

  **Must NOT do**:
  - device_class/state_classの誤設定
  - 単位の混在（WとkW、kWhとWh）
  - 15センサーすべてを実装（MVPは3のみ）

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []
  - **Reason**: 複数エンティティの実装とHA規約への準拠

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 7, Task 8
  - **Blocked By**: Task 3, Task 5

  **References**:
  - Task 2調査結果（Sensorパターン）
  - HA Sensor Docs: https://developers.home-assistant.io/docs/core/entity/sensor/
  - Energy Dashboard: https://www.home-assistant.io/docs/energy/

  **Acceptance Criteria**:
  - [ ] 3つのセンサークラス実装
  - [ ] device_class設定（power, energy, monetary）
  - [ ] state_class設定（measurement, total_increasing）
  - [ ] native_unit_of_measurement設定（W, kWh, JPY/kWh）
  - [ ] Energy Dashboardで認識される

  **QA Scenarios**:

  ```
  Scenario: センサー属性確認
    Tool: Bash (curl)
    Preconditions: インテグレーション設定済み
    Steps:
      1. curl http://localhost:8123/api/states/sensor.oejp_current_power
      2. device_class, state_class, unit_of_measurementを確認
    Expected Result: device_class=power, state_class=measurement, unit=W
    Evidence: .sisyphus/evidence/task-6-sensor-attrs.json
  
  Scenario: Energy Dashboard統合確認
    Tool: playwright
    Preconditions: Home Assistant起動済み
    Steps:
      1. Energy Dashboardを開く
      2. 「Grid Consumption」設定をクリック
      3. sensor.oejp_today_consumptionが選択肢に表示されることを確認
    Expected Result: センサーがEnergy Dashboardで使用可能
    Evidence: .sisyphus/evidence/task-6-energy-dashboard.png
  ```

  **Evidence to Capture**:
  - [ ] センサー属性のJSON
  - [ ] Energy Dashboardスクリーンショット
  - [ ] 実際の値の表示

  **Commit**: YES
  - Message: `feat: add MVP sensors (power, consumption, rate)`
  - Files: `custom_components/oejp_kraken/sensor.py`

- [ ] 7. 設定フロー・翻訳ファイル実装

  **What to do**:
  - `config_flow.py`実装（ConfigFlow継承）
  - ユーザー入力フォーム（メール、パスワード、更新間隔）
  - 入力バリデーション（メール形式、パスワード強度）
  - 接続テスト（認証確認）
  - `translations/ja.json`更新（日本語ラベル）
  - 設定オプション（更新間隔変更）

  **Must NOT do**:
  - バリデーションスキップ
  - 平文でのパスワード表示
  - YAML設定（Config Flowのみ）

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Reason**: 標準的なHAパターンに従う実装

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 8
  - **Blocked By**: Task 3, Task 6

  **References**:
  - Task 2調査結果（Config Flowパターン）
  - HA Config Flow Docs: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
  - Translations: https://developers.home-assistant.io/docs/internationalization/

  **Acceptance Criteria**:
  - [ ] ConfigFlowクラス実装
  - [ ] ユーザー入力フォーム（メール、パスワード）
  - [ ] 入力バリデーション
  - [ ] 接続テスト（認証成功確認）
  - [ ] translations/ja.json更新
  - [ ] OptionsFlow（更新間隔変更）

  **QA Scenarios**:

  ```
  Scenario: 設定フローUIテスト
    Tool: playwright
    Preconditions: Home Assistant起動済み
    Steps:
      1. 「設定」→「デバイスとサービス」→「統合を追加」
      2. 「OEJP Kraken」を選択
      3. メール・パスワードを入力
      4. 「送信」をクリック
    Expected Result: 認証成功、統合が追加される
    Evidence: .sisyphus/evidence/task-7-config-flow.png
  
  Scenario: 翻訳確認
    Tool: playwright
    Preconditions: 設定フロー表示中
    Steps:
      1. フォームのラベルが日本語であることを確認
    Expected Result: 「メールアドレス」「パスワード」など日本語表示
    Evidence: .sisyphus/evidence/task-7-translation.png
  ```

  **Evidence to Capture**:
  - [ ] 設定フローのスクリーンショット
  - [ ] 翻訳適用確認
  - [ ] バリデーションエラー表示

  **Commit**: YES
  - Message: `feat: add config flow and translations`
  - Files: `custom_components/oejp_kraken/config_flow.py`, `translations/ja.json`

- [ ] 8. HACS対応・ドキュメント作成

  **What to do**:
  - `hacs.json`作成（HACS設定）
  - `README.md`作成（インストール・設定ガイド）
  - `info.md`作成（HACS表示用）
  - `LICENSE`ファイル追加
  - GitHub Actions（オプション: リント、テスト）
  - スクリーンショット・デモ画像準備

  **Must NOT do**:
  - HACS要件を満たさない構造
  - 不完全なドキュメント

  **Recommended Agent Profile**:
  - **Category**: `writing`
  - **Skills**: []
  - **Reason**: ドキュメント作成とHACS要件対応

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 9
  - **Blocked By**: Task 6, Task 7

  **References**:
  - HACS Integration Requirements: https://hacs.xyz/docs/publish/integration/
  - HACS Default Repository: https://hacs.xyz/docs/publish/include/

  **Acceptance Criteria**:
  - [ ] hacs.json作成（name, content_in_root, filename等）
  - [ ] README.md作成（インストール手順、設定方法、センサー一覧）
  - [ ] info.md作成（HACS用短い説明）
  - [ ] LICENSEファイル（MIT推奨）
  - [ ] HACS要件チェックリスト確認

  **QA Scenarios**:

  ```
  Scenario: HACS要件確認
    Tool: Bash (cat)
  
  Preconditions: なし
  Steps:
      1. cat hacs.json
      2. cat README.md
      3. HACS要件をチェック
    Expected Result: すべてのHACS要件を満たす
    Evidence: .sisyphus/evidence/task-8-hacs-check.md
  ```

  **Evidence to Capture**:
  - [ ] HACS要件チェックリスト
  - [ ] README.mdプレビュー

  **Commit**: YES
  - Message: `docs: add HACS support and documentation`
  - Files: `hacs.json`, `README.md`, `info.md`, `LICENSE`

- [ ] 9. 統合テスト・検証

  **What to do**:
  - 実際のHome Assistantインスタンスでの動作確認
  - センサー値の正確性確認
  - トークンリフレッシュ動作確認
  - レート制限対応確認
  - Energy Dashboard統合確認
  - エラーハンドリング確認（無効な認証情報など）

  **Must NOT do**:
  - テストをスキップ
  - エラーケースの無視

  **Recommended Agent Profile**:
  - **Category**: `deep`
  - **Skills**: []
  - **Reason**: 包括的な動作確認とエッジケース検証

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4
  - **Blocks**: F1, F2
  - **Blocked By**: Task 8

  **References**:
  - すべての前タスク成果物
  - Home Assistant Testing: https://developers.home-assistant.io/docs/development_testing/

  **Acceptance Criteria**:
  - [ ] インテグレーションが正常にセットアップされる
  - [ ] 3つのセンサーが正しい値を表示
  - [ ] トークンが自動的にリフレッシュされる
  - [ ] Energy Dashboardで使用可能
  - [ ] エラー時に適切なメッセージが表示される

  **QA Scenarios**:

  ```
  Scenario: エンドツーエンドテスト
    Tool: playwright
    Preconditions: Home Assistant起動済み、有効なOEJPアカウント
    Steps:
      1. インテグレーションをセットアップ
      2. ダッシュボードにセンサーを追加
      3. 1時間待機（トークンリフレッシュ確認）
      4. 値が更新されることを確認
    Expected Result: すべての機能が正常に動作
    Evidence: .sisyphus/evidence/task-9-e2e-test.png
  
  Scenario: エラーハンドリングテスト
    Tool: playwright
    Preconditions: 無効な認証情報
    Steps:
      1. 誤ったパスワードでセットアップを試行
      2. エラーメッセージが表示されることを確認
    Expected Result: 適切なエラーメッセージ
    Evidence: .sisyphus/evidence/task-9-error.png
  ```

  **Evidence to Capture**:
  - [ ] ダッシュボードスクリーンショット
  - [ ] センサー値の確認
  - [ ] エラーメッセージ

  **Commit**: YES
  - Message: `test: add integration tests`
  - Files: `tests/`（オプション）

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** - `oracle`
  
  **What to verify**:
  - すべての「Must Have」が実装されているか
  - 「Must NOT Have」に該当するものがないか
  - 3センサーのみ実装（15センサーでない）
  - 非同期処理が正しく使用されているか
  - トークンが暗号化されているか
  
  **Acceptance Criteria**:
  - [ ] Must Have [8/8] 完了
  - [ ] Must NOT Have [6/6] 遵守
  - [ ] ファイル構造が正しい
  - [ ] HACS要件を満たす
  
  **Output**: `Must Have [8/8] | Must NOT Have [6/6] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** - `unspecified-high`
  
  **What to verify**:
  - Pythonコードスタイル（PEP8）
  - 型ヒントの使用
  - Docstringの有無
  - 不要なimportがないか
  - エラーハンドリングの網羅性
  
  **Acceptance Criteria**:
  - [ ] flake8/pylintパス
  - [ ] 型ヒントが主要関数に付与されている
  - [ ] 公開メソッドにDocstringがある
  
  **Output**: `Style [PASS/FAIL] | Types [PASS/FAIL] | Docs [PASS/FAIL] | VERDICT`

---

## Commit Strategy

| Wave | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat: initial integration structure` | `manifest.json`, `const.py`, `__init__.py`, `translations/ja.json` |
| 2 | `feat: add graphql client with auth` | `graphql_client.py` |
| 2 | `feat: add data update coordinator` | `coordinator.py` |
| 3 | `feat: add MVP sensors (power, consumption, rate)` | `sensor.py` |
| 3 | `feat: add config flow and translations` | `config_flow.py`, `translations/ja.json` |
| 4 | `docs: add HACS support and documentation` | `hacs.json`, `README.md`, `info.md`, `LICENSE` |
| 4 | `test: add integration tests` | `tests/` |

---

## Success Criteria

### Verification Commands
```bash
# 1. ファイル構造確認
ls -la custom_components/oejp_kraken/

# 2. manifest.json確認
cat custom_components/oejp_kraken/manifest.json | jq .

# 3. HACS要件確認
[[ -f hacs.json ]] && [[ -f README.md ]] && [[ -f LICENSE ]] && echo "OK"

# 4. センサー属性確認（HA起動後）
curl -s http://localhost:8123/api/states/sensor.oejp_current_power | jq '.attributes.device_class, .attributes.state_class'

# 5. Energy Dashboard統合確認
curl -s http://localhost:8123/api/states/sensor.oejp_today_consumption | jq '.attributes.device_class'
# Expected: "energy"
```

### Final Checklist
- [ ] 3つのMVPセンサーが動作
- [ ] メール/パスワード認証が機能
- [ ] トークン自動リフレッシュが動作
- [ ] Energy Dashboardで使用可能
- [ ] HACSからインストール可能
- [ ] 日本語UIが表示される
- [ ] エラーハンドリングが適切
- [ ] レート制限に対応

---

## Notes

### API仕様メモ
- **Endpoint**: `https://api.oejp-kraken.energy/v1/graphql/`
- **Auth**: ObtainKrakenTokenミューテーション
- **Token Lifetime**: Access=60min, Refresh=7days
- **Rate Limit**: 50,000ポイント/時間
- **Query Complexity**: Max 200
- **Node Limit**: Max 10,000

### Home Assistant互換性
- **Minimum Version**: 2023.7.0（推奨: 最新）
- **Python**: 3.11+
- **Dependencies**: aiohttp>=3.8.0

### 将来拡張（v2以降）
- 追加センサー（昨日/今月/先月の消費量）
- 複数アカウント対応
- 複数供給ポイント（SPIN）対応
- スマートデバイス制御（SmartFlex）
- 需給調整（Demand Response）
