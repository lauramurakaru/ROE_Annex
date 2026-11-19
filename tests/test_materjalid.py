"""Materjalide sünkrooni testid.

Kontrollime kahte asja:
1. iga LEGAD-i reegel viitab Grete IHL-registris olemasolevale nõudele;
2. vananenud õigusviite kontroll töötab (RiKS/RSKS -> KORKS).
"""
from pathlib import Path

import yaml

from faktid import kogu_faktid
from materjalid.grete.ihl_nouded import nouded
from reeglid import REEGLID_FAIL, hinda

from konfig import NAIDIS


def _reeglid() -> list[dict]:
    with open(REEGLID_FAIL, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _leid(leiud, id_):
    return next(l for l in leiud if l.id == id_)


def test_iga_reegel_viitab_ihl_registrile():
    registri_id_d = {n["id"] for n in nouded()}
    for r in _reeglid():
        assert "ihl_id" in r, f"{r['id']} ei viita IHL-registrile"
        for viide in str(r["ihl_id"]).split(","):
            viide = viide.strip()
            if viide:
                assert viide in registri_id_d, f"{r['id']}: tundmatu {viide}"


def test_registris_on_47_nouet():
    assert len(nouded()) == 47


def test_vananenud_viide_annab_kollase():
    f = kogu_faktid(NAIDIS)
    f.opord_tekst += "\nVt Riigikaitseseadus § 12 ja RSKS."
    l = _leid(hinda(f), "L02")
    assert l.staatus == "kollane"
    assert "Riigikaitseseadus" in l.kirjeldus


def test_kehtiv_kask_ei_anna_vananenud_viite_leidu():
    f = kogu_faktid(NAIDIS)
    l = _leid(hinda(f), "L02")
    assert l.staatus == "roheline"
