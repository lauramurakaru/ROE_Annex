"""LEGAD lisa .docx test.

Kontrollime, et dokument oleks terviklik: kolm põhimõtet, leidude tabel,
allikad igal leiul, allkirjad ja MUSTAND-i hoiatus.
"""
from pathlib import Path

import docx

from faktid import kogu_faktid
from lisa import koosta_docx
from reeglid import hinda

from konfig import NAIDIS


def _tekst(p: Path) -> str:
    d = docx.Document(str(p))
    osad = [x.text for x in d.paragraphs]
    for t in d.tables:
        for r in t.rows:
            osad.extend(c.text for c in r.cells)
    return "\n".join(osad)


def test_docx_luuakse_ja_sisu(tmp_path):
    f = kogu_faktid(NAIDIS)
    leiud = hinda(f)
    p = koosta_docx(leiud, f, tmp_path / "legad_lisa.docx")
    assert p.exists() and p.stat().st_size > 2000

    tekst = _tekst(p)
    assert "MUSTAND" in tekst
    assert "ERISTAMINE" in tekst
    assert "PROPORTSIONAALSUS" in tekst
    assert "SÕJALINE VAJADUS" in tekst
    assert "T3" in tekst
    assert "AP I art 53" in tekst
    assert "Sanremo" in tekst
    assert "LOAC manual" not in tekst
    assert "Operational Law" not in tekst
    assert "LEGAD" in tekst
    assert "Komandör" in tekst


def test_docx_ei_leiuta_uusi_sihtmarke(tmp_path):
    f = kogu_faktid(NAIDIS)
    leiud = hinda(f)
    p = koosta_docx(leiud, f, tmp_path / "legad_lisa.docx")
    tekst = _tekst(p)
    for vale in ("SM5", "SM6", "T4", "T5"):
        assert vale not in tekst


def test_docx_bytes_alla_laadimiseks():
    from lisa import docx_bytes

    f = kogu_faktid(NAIDIS)
    andmed = docx_bytes(hinda(f), f)
    assert andmed[:2] == b"PK"
    assert len(andmed) > 2000
