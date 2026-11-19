"""LEGAD lisa .docx väljund.

Struktuur: päis + kokkuvõttev leiutabel + kolm põhimõtet + allkirjad.
Iga leid sisaldab käsu kohta, õiguslikku alust ja soovitust — nii saab LEGAD
seda kontrollida ilma tööriista usaldamata.
"""
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from faktid import Faktid
from reeglid import Leid
from allikad import ALLIKAD, EI_KASITA

OSAD = [
    ("1. ÕIGUSLIK ALUS JA REŽIIM", "õiguslik alus"),
    ("2. ERISTAMINE", "eristamine"),
    ("3. PROPORTSIONAALSUS", "proportsionaalsus"),
    ("4. SÕJALINE VAJADUS", "sõjaline vajadus"),
]

STAATUSE_JARJ = {"punane": 0, "kollane": 1, "roheline": 2}


def _pais(d, f: Faktid, leiud: list[Leid]) -> None:
    t = d.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("LEGAD LISA – ÕIGUSLIK HINNANG")
    r.bold = True
    r.font.size = Pt(16)

    t = d.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("MUSTAND – kinnitab LEGAD, mitte tööriist")
    r.italic = True
    r.font.size = Pt(10)

    d.add_paragraph(
        f"Allikas: {f.opord_allikas} ja lisad. Koostatud: "
        f"{date.today().strftime('%d.%m.%Y')}. Reegleid: {len(leiud)} kontrolli."
    )
    p = d.add_paragraph()
    p.add_run("Lühikokkuvõte: ").bold = True
    p.add_run(
        f"{sum(1 for l in leiud if l.staatus == 'punane')} punast, "
        f"{sum(1 for l in leiud if l.staatus == 'kollane')} kollast, "
        f"{sum(1 for l in leiud if l.staatus == 'roheline')} rohelist leidu. "
        "Punased ja kollased leiud tuleb lahendada enne käsu kinnitamist."
    )


def _kokkuvote_tabel(d, leiud: list[Leid]) -> None:
    d.add_heading("LEIDUDE KOKKUVÕTE", level=1)
    tabel = d.add_table(rows=1, cols=4)
    tabel.style = "Table Grid"
    for i, pealkiri in enumerate(("ID", "Põhimõte", "Staatus", "Käsu koht")):
        tabel.rows[0].cells[i].text = pealkiri
        for p in tabel.rows[0].cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
    for l in sorted(leiud, key=lambda x: (STAATUSE_JARJ.get(x.staatus, 9), x.id)):
        rida = tabel.add_row().cells
        rida[0].text = l.id
        rida[1].text = l.pohimote
        rida[2].text = l.staatus
        rida[3].text = l.koht


def _leiud(d, leiud: list[Leid]) -> None:
    for pealkiri, pohimote in OSAD:
        d.add_heading(pealkiri, level=1)
        grupp = [l for l in leiud if l.pohimote == pohimote]
        if not grupp:
            d.add_paragraph("Selles osas leide ei ole.")
            continue
        for l in grupp:
            h = d.add_heading(f"{l.id} – {l.pealkiri}", level=2)
            for r in h.runs:
                r.font.size = Pt(11)
            tabel = d.add_table(rows=0, cols=2)
            tabel.style = "Table Grid"
            read = [
                ("Staatus", l.staatus.upper()),
                ("Käsu koht", l.koht),
                ("Kirjeldus", l.kirjeldus),
                ("Õiguslik alus", l.allikas),
            ]
            if l.ihl_id:
                read.append(("IHL nõue", l.ihl_id))
            read += [
                ("Soovitus", l.soovitus),
                ("Kinnitab", l.kinnitaja),
            ]
            for nimi, sisu in read:
                rida = tabel.add_row().cells
                rida[0].text = nimi
                rida[1].text = sisu
                for p in rida[0].paragraphs:
                    for r in p.runs:
                        r.bold = True
            d.add_paragraph()


def _allikad(d) -> None:
    d.add_heading("5. ALLIKAD JA KATVUS", level=1)
    tabel = d.add_table(rows=1, cols=3)
    tabel.style = "Table Grid"
    for i, pealkiri in enumerate(("Allikas", "Viide", "Mida katab")):
        tabel.rows[0].cells[i].text = pealkiri
        for p in tabel.rows[0].cells[i].paragraphs:
            for r in p.runs:
                r.bold = True
    for a in ALLIKAD:
        rida = tabel.add_row().cells
        rida[0].text = a["nimi"]
        rida[1].text = a["viide"]
        rida[2].text = a["mida"]
    d.add_paragraph()
    p = d.add_paragraph()
    p.add_run("Teadlikult katmata selles lisas: ").bold = True
    p.add_run("; ".join(EI_KASITA) + ".")


def _allkirjad(d) -> None:
    d.add_heading("6. KINNITUSED", level=1)
    d.add_paragraph(
        "Käesolev dokument on LEGAD-i töövahendi koostatud mustand. Lõpliku "
        "õigusliku hinnangu annab ja allkirjastab LEGAD."
    )
    tabel = d.add_table(rows=2, cols=3)
    tabel.style = "Table Grid"
    paised = ("Roll", "Nimi / allkiri", "Kuupäev")
    for i, p in enumerate(paised):
        tabel.rows[0].cells[i].text = p
        for par in tabel.rows[0].cells[i].paragraphs:
            for r in par.runs:
                r.bold = True
    tabel.rows[1].cells[0].text = "LEGAD"
    tabel.rows[1].cells[1].text = "____________________"
    tabel.rows[1].cells[2].text = "__________"
    rida = tabel.add_row().cells
    rida[0].text = "Komandör"
    rida[1].text = "____________________"
    rida[2].text = "__________"


def _koosta(leiud: list[Leid], f: Faktid):
    d = docx.Document()
    stiil = d.styles["Normal"]
    stiil.font.name = "Arial"
    stiil.font.size = Pt(10)

    _pais(d, f, leiud)
    _kokkuvote_tabel(d, leiud)
    _leiud(d, leiud)
    _allikad(d)
    _allkirjad(d)
    return d


def koosta_docx(leiud: list[Leid], f: Faktid, valjund: str | Path) -> Path:
    valjund = Path(valjund)
    valjund.parent.mkdir(parents=True, exist_ok=True)
    _koosta(leiud, f).save(str(valjund))
    return valjund


def docx_bytes(leiud: list[Leid], f: Faktid) -> bytes:
    puhver = BytesIO()
    _koosta(leiud, f).save(puhver)
    return puhver.getvalue()
