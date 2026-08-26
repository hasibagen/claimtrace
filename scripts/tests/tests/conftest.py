"""pytest 共享配置:把 .skill/scripts 与 schemas 加入 sys.path。"""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
for p in (SCRIPTS, SCRIPTS / "schemas"):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
