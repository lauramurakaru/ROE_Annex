"""Failide lugemine: .docx ja .xlsx -> puhas tekst / read.

Hoiame selle eraldi, et faktide eraldamine (faktid.py) oleks testitav
ilma failivormingute detailidesse süvenemata.
"""
from __future__ import annotations

from pathlib import Path

import docx
import openpyxl


def loe_docx(path: str | Path) -> str:
    """Tagastab dokumendi tekstina: lõigud + tabeliread (| eraldatud)."""
    d = docx.Document(str(path))
    read: list[str] = []
    for p in d.paragraphs:
        t = p.text.strip()
        if t:
            read.append(t)
    for tabel in d.tables:
        for rida in tabel.rows:
            lahtrid = [c.text.strip() for c in rida.cells]
            if any(lahtrid):
                read.append(" | ".join(lahtrid))
    return "\n".join(read)


def _lahter(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def loe_xlsx(path: str | Path) -> list[dict[str, str]]:
    """Tagastab töölehe read sõnastikena (esimene rida = päised).

    Kui päiseid ei ole, kasutatakse võtmeid veerus1, veerus2, ...
    """
    wb = openpyxl.load_workbook(str(path), data_only=True)
    ws = wb.active
    read = [[_lahter(v) for v in rida] for rida in ws.iter_rows(values_only=True)]
    read = [r for r in read if any(r)]
    if not read:
        return []
    paised = [p or f"veerg{i + 1}" for i, p in enumerate(read[0])]
    tulemus: list[dict[str, str]] = []
    for rida in read[1:]:
        rida = rida + [""] * (len(paised) - len(rida))
        tulemus.append({p: v for p, v in zip(paised, rida)})
    return tulemus
