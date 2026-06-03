# QNEAT3 NEO — コード追跡・呼び出し整合

設計段階で「定義と参照の不一致」を潰すための正本。ZIP 作成前に `scripts/validate_all_symbol_refs.py` を必ず実行する。

## 1. シンボル台帳（単一ソース）

| 台帳 | 定義ファイル | 参照パターン | 検証 |
|------|--------------|--------------|------|
| UI ラベル | `Qneat3Strings.UIS` | `ja(UIS.*)` | validate_all_symbol_refs |
| ログ | `Qneat3Strings.LOG` | `log_msg(feedback, LOG.*, ...)` | 同上 |
| エラー | `Qneat3Strings.ERR` | `ja(ERR.*)` | 同上 |
| ヘルプ HTML | `Qneat3HelpJa.help_*` | `help_*()` in `shortHelpString` | 同上 |

**禁止:** `algs/*.py` で `self.tr(UIS.xxx)`（`ja()` を使う）。一括置換スクリプト実行後は必ず検証。

### UIS 出力名（正規 + 別名）

| 正規名 | 別名（後方互換） | 用途 |
|--------|------------------|------|
| `OUTPUT_POINTCLOUD` | `OUTPUT_ISO_POINTCLOUD` | 等時点クラウド出力 |
| `OUTPUT_CONTOURS` | `OUTPUT_ISO_CONTOURS` | 等値線出力 |
| `OUTPUT_POLYGONS` | `OUTPUT_ISO_POLYGONS` | ポリゴン出力 |

## 2. 起動・登録フロー（Processing プロバイダ）

```mermaid
sequenceDiagram
    participant QGIS
    participant Plugin as Qneat3Plugin
    participant Prov as Qneat3Provider
    participant Algs as algs/__init__.py
    participant Alg as ShortestPathBetweenPoints

    QGIS->>Plugin: initProcessing()
    Plugin->>Prov: Qneat3Provider()
    Plugin->>QGIS: processingRegistry().addProvider(Prov)
    Prov->>Prov: loadAlgorithms()
    Note over Prov,Algs: from QNEAT3.algs import Class（モジュールではない）
    Prov->>Alg: ShortestPathBetweenPoints()
    Prov->>QGIS: addAlgorithm(instance)
    Note over Prov: NG: ShortestPathBetweenPoints.ShortestPathBetweenPoints()
```

## 3. 典型アルゴリズム実行フロー（最短経路）

```mermaid
flowchart TD
    A[processAlgorithm] --> B[log_msg LOG.ALG_START]
    B --> C[read parameters]
    C --> D[Qneat3Framework.setup]
    D --> E[setNetworkStrategy link_len or speed]
    E --> F[build graph]
    F --> G[shortestPath]
    G --> H{path found?}
    H -->|No| I[QgsProcessingException ja ERR.NO_PATH]
    H -->|Yes| J[write feature + cost log]
    J --> K[log_msg LOG.ALG_END]
```

## 4. initAlgorithm フェーズ（パラメータ UI）

```mermaid
flowchart LR
    subgraph once [QGIS が一度だけ呼ぶ]
        I[initAlgorithm] --> P1[ja UIS.NETWORK_LAYER]
        P1 --> P2[ja UIS.OPTIMIZATION_CRITERION]
        P2 --> P3[add_advanced_network_params]
        P3 --> P4[ja UIS.OUTPUT_*]
    end
    subgraph run [実行のたび]
        R[processAlgorithm] --> S[strategy index → link_len or speed]
    end
    once -.->|UI は変わらない| run
```

**仕様:** 最適化基準を変えても `initAlgorithm` は再実行されない → パラメータ一覧は固定。コストは `processAlgorithm` 内の `Qneat3Framework` で切替。

## 5. 距離最適化 vs 時間最適化（コストの使い分け）

| 要素 | strategy=0 最短距離 | strategy=1 最速 |
|------|---------------------|-----------------|
| グラフ辺コスト | `Qneat3LinkLengthStrategy`（link_len） | `Qneat3LinkLengthTimeStrategy`（link_len÷速度） |
| 速度フィールド | **未使用** | 使用（無効時はデフォルト速度） |
| デフォルト速度 | **未使用**（0 可） | **必須**（正の km/h、接続コストにも使用） |
| 接続コスト（entry/exit） | **距離**（m） | 実測直線距離÷速度（時間） |

式の詳細: [COST_FORMULAS.md](COST_FORMULAS.md)

```mermaid
flowchart TD
    S[STRATEGY パラメータ] -->|0| D[setNetworkStrategy distance]
    S -->|1| T[setNetworkStrategy time]
    D --> L[link_len 検証 + Qneat3LinkLengthStrategy]
    D --> I[速度パラメータは無視・ログ NET_DISTANCE_SKIPS_SPEED]
    T --> V[default_speed > 0 必須]
    T --> SP[Qneat3LinkLengthTimeStrategy]
```

## 6. 以前の監査で漏れた理由（再発防止）

| 実施していたこと | 漏れていたこと |
|------------------|----------------|
| link_len / 戦略のロジック追跡 | `UIS.*` **定義台帳と参照の機械照合** |
| Processing UI が変わらない件の仕様確認 | 一括置換スクリプトと `Qneat3Strings.py` の**同期** |
| Provider `addAlgorithm` の手動修正 | ZIP 前の**自動ゲート** |

**対策:** `pack_plugin_zip.ps1` → `validate_metadata.py` + **`validate_all_symbol_refs.py`** を必須化。

## 7. link_len エラー（方針 B）

| コード | ERR 定数 | 条件 |
|--------|----------|------|
| FIELD_NAME_EMPTY | `ERR.LINK_LEN_FIELD_EMPTY` | フィールド名未指定 |
| FIELD_NOT_IN_LAYER | `ERR.LINK_LEN_FIELD_MISSING` | レイヤにフィールドなし |
| VALUE_NULL | `ERR.LINK_LEN_VALUE_NULL` | NULL / 空 |
| VALUE_NOT_NUMERIC | `ERR.LINK_LEN_VALUE_NOT_NUMERIC` | 数値化不可 |
| VALUE_NOT_POSITIVE | `ERR.LINK_LEN_VALUE_NOT_POSITIVE` | 0 以下 |

実装: `Qneat3NetworkErrors.py` → `QgsProcessingException(ERR.LINK_LEN_HEADER + …)`  
距離最適化のみ。時間最適化の速度 0 は `ERR.DEFAULT_SPEED_INVALID`（距離時は検証しない）。

## 8. チェックコマンド

```powershell
python H:\CURSOR\QNEAT3\scripts\validate_all_symbol_refs.py
python H:\CURSOR\QNEAT3\scripts\validate_network_errors.py
python H:\CURSOR\QNEAT3\scripts\verify_provider_register.py
python H:\CURSOR\QNEAT3\scripts\validate_metadata.py
```

すべて exit 0 のあと ZIP 作成。
