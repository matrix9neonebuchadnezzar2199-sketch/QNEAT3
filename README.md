# QNEAT3 NEO

**ドキュメント（導入・使い方・バグ調査）は HTML 版を参照してください:**

→ **[README.html](README.html)**（ブラウザで開く）

## クイックメモ

- 配置先フォルダ名: **`QNEAT3`**（`plugins\QNEAT3\`）
- 距離最適化: エッジコスト = **`link_len` × (セグメント長/リンク全長)** [m]（全リンク必須、リンク合計 = link_len）
- 時間最適化: 上記按分 **÷ 速度** [s]（形状長は未使用）
- 点座標: 経緯度はそのまま入力可（みなし変換・1.0.24）
- 計算式: [docs/COST_FORMULAS.md](docs/COST_FORMULAS.md)
- リポジトリ: https://github.com/matrix9neonebuchadnezzar2199-sketch/QNEAT3

## 「プラグインが壊れています」／再インストールで元に戻る

公式の **再インストール** は使わず、クリーン導入してください。詳細は [README.html#plugin-broken](README.html#plugin-broken)

## 開発者向け品質チェック（QGIS 不要）

パック／コミット前にリポジトリルートで実行:

```powershell
python TEST.py
```

構文・UTF-8・シンボル参照・アイコン存在・Provider 登録・link_len パーサ単体テストを一括実行します。

コンテナ実機スモーク（「QGIS検証」、`docker/README.md`）:

```powershell
docker build -f docker/Dockerfile -t qgis-neo-verify:latest .
docker run --rm -v "${PWD}\docker\out:/out" qgis-neo-verify:latest
```

## 検証手順（STEPS）

更新反映・`link_len` 動作・距離/時間切替の確認手順は HTML 版に記載:

→ **[README.html#verify-steps](README.html#verify-steps)**

詳細は [README.html](README.html) を参照。
