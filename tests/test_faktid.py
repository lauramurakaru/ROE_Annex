"""Faktide eraldamine näidiskomplektist.

Testid on kirjutatud enne koodi. Oodatud väärtused on loetud käsitsi
`siim/naidis/brigaadi_kask/` failidest.
"""
from pathlib import Path

from faktid import kogu_faktid

from konfig import NAIDIS


def _faktid():
    return kogu_faktid(NAIDIS)


def test_opord_tekst_loetakse():
    f = _faktid()
    assert "MISSIOON" in f.opord_tekst
    assert "KIVI–SAARE" in f.opord_tekst


def test_neli_sihtmarki():
    f = _faktid()
    assert [s.id for s in f.sihtmarkid] == ["SM1", "SM2", "SM3", "SM4"]
    sm1 = f.sihtmarkid[0]
    assert sm1.aeg == "H+6"
    assert "maanteel nr 3" in sm1.kirjeldus
    assert sm1.vahend == "STV patarei"


def test_kolm_toket():
    f = _faktid()
    assert [t.id for t in f.tokked] == ["T1", "T2", "T3"]
    t3 = f.tokked[2]
    assert "SAARE kirik" in t3.asukoht
    assert t3.oigus == "pataljon"


def test_kaitstud_objektid():
    f = _faktid()
    nimed = {o.nimi for o in f.objektid}
    assert any("haigla" in n.lower() for n in nimed)
    assert any("kirik" in n.lower() for n in nimed)
    assert any("sild" in n.lower() for n in nimed)

    kirik = next(o for o in f.objektid if "kirik" in o.nimi.lower())
    assert kirik.liik == "kirik"
    assert kirik.meditsiinipunkt is True
    assert kirik.kaitstud is True

    haigla = next(o for o in f.objektid if "haigla" in o.nimi.lower())
    assert haigla.liik == "haigla"
    assert haigla.kaitstud is True


def test_tsiviilid_ja_evakuatsioon():
    f = _faktid()
    assert f.tsiviilide_arv == 400
    assert f.evakuatsiooni_aeg == "H+2"
    assert f.hoiatus and "maanteed nr 3" in f.hoiatus


def test_tuleajad():
    f = _faktid()
    assert "H+6" in f.tuleajad
    assert "H+7" in f.tuleajad


def test_reziim_puudub_käsust():
    f = _faktid()
    assert f.reziim is None
    assert f.opord_allikas.endswith("01_Brigaadi_OPORD_1JVP.docx")
