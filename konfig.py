"""Ühine konfiguratsioon: kus on näidiskomplekt.

Tööriist on iseseisev: näidisandmed on kaustas `naidis/brigaadi_kask/`.
"""
from pathlib import Path

JUUR = Path(__file__).resolve().parent
NAIDIS = JUUR / "naidis" / "brigaadi_kask"
