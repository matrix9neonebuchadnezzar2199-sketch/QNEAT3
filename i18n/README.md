# QNEAT3_NEO 日本語化

## 動作

- UI 文言は `Qneat3Strings.py` の日本語を `self.tr()` に渡す方式（`.qm` なしでも日本語表示）。
- QGIS の UI 言語が日本語のとき、`qneat3_ja.qm` があれば上書き翻訳も可能。

## .qm のビルド（任意）

OSGeo4W Shell 等で:

```bat
cd path\to\plugins\QNEAT3\i18n
lrelease qneat3_ja.ts -qm qneat3_ja.qm
```

`lrelease` は Qt ツール（QGIS 同梱の OSGeo4W に含まれる場合あり）。

## プラグイン配置

Python の import は `QNEAT3` パッケージ名のため、配置先フォルダ名は **`QNEAT3`** にリネームすること。
