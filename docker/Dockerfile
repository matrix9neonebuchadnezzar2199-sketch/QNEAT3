# QGIS検証 — QNEAT3 NEO スモークテスト環境
# 公式 qgis/qgis イメージ + qgis_process でプラグインの実機検証を行う。
# 既存の Docker 資産には干渉しない（イメージ名 qgis-neo-verify 固定）。
FROM qgis/qgis:stable

ENV QT_QPA_PLATFORM=offscreen \
    QGIS_PLUGINPATH=/opt/plugins

# プラグイン（フォルダ名 QNEAT3 必須）をプラグイン検索パスに配置
COPY . /opt/plugins/QNEAT3

# 検証スクリプト・テストデータ
COPY docker/ /opt/qneat3-test/

# Windows チェックアウトの CRLF 対策（bash は CR があると壊れる）
RUN sed -i 's/\r$//' /opt/qneat3-test/run_smoke.sh \
    && chmod +x /opt/qneat3-test/run_smoke.sh

CMD ["bash", "/opt/qneat3-test/run_smoke.sh"]
