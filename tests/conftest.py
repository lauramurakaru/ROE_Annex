import sys
from pathlib import Path

JUUR = Path(__file__).resolve().parents[1]
if str(JUUR) not in sys.path:
    sys.path.insert(0, str(JUUR))
