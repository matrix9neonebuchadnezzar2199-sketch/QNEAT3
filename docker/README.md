# QGIS検証 — QNEAT3 NEO スモークテスト環境

公式 `qgis/qgis` イメージ上の `qgis_process` で、NEO プラグインの実機動作を
ローカル QGIS を汚さずに自動検証する。

## 安全性（他の Docker 資産に触れない）

- 使う名前はすべて `qgis-neo-verify` 固定（イメージ・コンテナ・compose プロジェクト）
- `docker system prune` / `docker rm` / `docker rmi` 等の一括削除は**実行しない**
- 出力は `./out`（このフォルダ内）へのみ書き込む。名前付きボリュームは使わない
- 片付けは `docker image rm qgis-neo-verify` のみ（他のイメージ・コンテナに無関係）

## 使い方

```powershell
cd H:\CURSOR\QNEAT3

# ビルド（初回は公式イメージ取得で時間がかかる）
docker build -f docker/Dockerfile -t qgis-neo-verify:latest .

# スモーク実行（結果は docker/out に出る）
docker run --rm -v "${PWD}\docker\out:/out" qgis-neo-verify:latest
```

compose を使う場合:

```powershell
cd H:\CURSOR\QNEAT3\docker
docker compose up --build
```

終了コード 0 かつ `SMOKE PASS` が出れば成功。

## 検証内容（docker/testdata/network.geojson）

| ステップ | 内容 | 判定 |
|---|---|---|
| 1 | `qgis_process list` に `qneat3:networkpreparelinks` | Provider 登録 |
| 2 | ネットワーク前処理を実行 | T 字突き当たりの架空道路で既存リンクを分割 |
| 3 | 出力の `link_len` | base 5000 → 2500×2（按分）、架空 300（保持）、NULL → 実測 ≈100（補完） |
| 4 | 最短経路（距離）(500,1000)→(0,0) | 架空道路経由で `cost = 2800`（300 + 2500） |
| 5 | 最短経路（時間・速度フィールド） | 架空 300 m @5km/h = 216 s + base 2500 m @100km/h = 90 s → `cost = 306 s` |
| 6 | OD 行列（ポイント・ライン n:n、経路ジオメトリ） | A↔B 双方向 `network_cost = 2800`＋経路ジオメトリ非空 |

## 制約

- GUI 相当の確認は対象外（`QT_QPA_PLATFORM=offscreen` のヘッドレス実行）
- matplotlib は入れていないため等時圏の等高線系は Dummy 登録になる（既定挙動）
- イメージタグは `qgis/qgis:stable`。再現性を厳密にする場合はバージョン固定タグに変える
