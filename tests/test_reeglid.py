"""Reeglimootori testid näidiskäsu peal.

Oodatud leiud on tuletatud käsitsi: OPORD + lisad D, E, J sisu vastu
AP I artiklitele. Test kirjutati enne mootorit.
"""
from pathlib import Path

import pytest

from faktid import kogu_faktid
from reeglid import hinda

from konfig import NAIDIS


@pytest.fixture(scope="module")
def leiud():
    return hinda(kogu_faktid(NAIDIS))


def _leid(leiud, id_):
    for l in leiud:
        if l.id == id_:
            return l
    raise AssertionError(f"leidu {id_} ei ole: {[x.id for x in leiud]}")


def test_reziim_puudub_on_punane(leiud):
    l = _leid(leiud, "L01")
    assert l.staatus == "punane"
    assert "KKS" in l.allikas


def test_toke_kiriku_juures_on_punane(leiud):
    l = _leid(leiud, "E01")
    assert l.staatus == "punane"
    assert "T3" in l.koht
    assert "AP I art 53" in l.allikas
    assert "meditsiinipunkt" in l.kirjeldus.lower()


def test_sihtmarkide_tuvastus_on_kollane(leiud):
    l = _leid(leiud, "E02")
    assert l.staatus == "kollane"
    assert "SM1" in l.koht and "SM3" in l.koht and "SM4" in l.koht
    assert "57" in l.allikas


def test_maantee_lohkamine_vajab_pohjendust(leiud):
    l = _leid(leiud, "E03")
    assert l.staatus == "kollane"
    assert "T1" in l.koht


def test_tsiviilkahju_hinnang_puudub(leiud):
    l = _leid(leiud, "P01")
    assert l.staatus == "kollane"
    assert "400" in l.kirjeldus
    assert "51" in l.allikas


def test_evakuatsiooni_lopp_on_kontrollimata(leiud):
    l = _leid(leiud, "P02")
    assert l.staatus == "kollane"
    assert "H+2" in l.kirjeldus


def test_hoiatuse_kanal_puudub(leiud):
    l = _leid(leiud, "P03")
    assert l.staatus == "kollane"
    assert "kanal" in l.kirjeldus.lower()


def test_katkestamise_kriteerium_puudub(leiud):
    l = _leid(leiud, "P05")
    assert l.staatus == "kollane"


def test_tokke_eesmark_ja_alternatiiv(leiud):
    l = _leid(leiud, "V01")
    assert l.staatus == "kollane"
    assert "T1" in l.koht


def test_sm4_eesmark_on_kirjas_roheline(leiud):
    l = _leid(leiud, "V02")
    assert l.staatus == "roheline"


def test_evakuatsioon_on_korraldatud_roheline(leiud):
    l = _leid(leiud, "V06")
    assert l.staatus == "roheline"
    assert "Päästeamet" in l.kirjeldus


def test_igal_leiul_on_allikas_ja_soovitus(leiud):
    assert len(leiud) >= 10
    for l in leiud:
        assert l.staatus in {"punane", "kollane", "roheline"}
        assert l.allikas.strip()
        assert l.soovitus.strip()
        assert l.pohimote in {
            "õiguslik alus",
            "eristamine",
            "proportsionaalsus",
            "sõjaline vajadus",
        }


def test_roe_puudub_on_punane(leiud):
    l = _leid(leiud, "L03")
    assert l.staatus == "punane"
    assert "ROE" in l.kirjeldus


def test_roe_viide_annab_rohelise():
    f = kogu_faktid(NAIDIS)
    f.opord_tekst += "\nROE: jõudu kasutada ainult enesekaitseks."
    l = _leid(hinda(f), "L03")
    assert l.staatus == "roheline"
    assert "enesekaitse" in l.kirjeldus


def test_roe_piirang_margitakse_poliitikana():
    f = kogu_faktid(NAIDIS)
    f.opord_tekst += "\nROE: jõudu kasutada ainult enesekaitseks."
    l = _leid(hinda(f), "L04")
    assert l.staatus == "kollane"
    assert "poliitika" in l.kirjeldus.lower()

