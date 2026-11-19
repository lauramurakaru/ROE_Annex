"""Robustsus: failid ei pea olema näidise nimedega.

Kui kasutaja laadib üles 4 faili (OPORD + lisa D, E, J) teiste nimedega,
peab tööriist need sisu järgi ära tundma.
"""
import shutil
from pathlib import Path

from faktid import kogu_faktid

from konfig import NAIDIS


def _koopia(tmp_path: Path, uued_nimed: dict[str, str]) -> Path:
    for vana, uus in uued_nimed.items():
        shutil.copy2(NAIDIS / vana, tmp_path / uus)
    return tmp_path


def test_ümbernimetud_neli_faili(tmp_path):
    _koopia(tmp_path, {
        "01_Brigaadi_OPORD_1JVP.docx": "kask.docx",
        "Lisa_D_tuletoetus.xlsx": "sihtmargid.xlsx",
        "Lisa_E_pioneer.xlsx": "tokked.xlsx",
        "Lisa_J_CIMIC.docx": "cimic.docx",
    })
    f = kogu_faktid(tmp_path)
    assert f.opord_allikas == "kask.docx"
    assert [s.id for s in f.sihtmarkid] == ["SM1", "SM2", "SM3", "SM4"]
    assert [t.id for t in f.tokked] == ["T1", "T2", "T3"]
    assert f.tsiviilide_arv == 400
    assert f.leitud_failid["D"] == "sihtmargid.xlsx"
    assert f.leitud_failid["J"] == "cimic.docx"


def test_leiab_ka_originaalnimedega(tmp_path):
    _koopia(tmp_path, {
        "01_Brigaadi_OPORD_1JVP.docx": "01_Brigaadi_OPORD_1JVP.docx",
        "Lisa_D_tuletoetus.xlsx": "Lisa_D_tuletoetus.xlsx",
        "Lisa_E_pioneer.xlsx": "Lisa_E_pioneer.xlsx",
        "Lisa_J_CIMIC.docx": "Lisa_J_CIMIC.docx",
    })
    f = kogu_faktid(tmp_path)
    assert f.leitud_failid["opord"] == "01_Brigaadi_OPORD_1JVP.docx"
    assert f.leitud_failid["E"] == "Lisa_E_pioneer.xlsx"
