# -*- coding: utf-8 -*-
"""リポジトリルートから品質チェックを実行するエントリ。"""
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SCRIPT = _ROOT / "scripts" / "test_quality.py"
sys.exit(subprocess.call([sys.executable, str(_SCRIPT)], cwd=str(_ROOT.parent)))
