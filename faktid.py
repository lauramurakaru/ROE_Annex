"""Faktide eraldamine OPORD-i komplektist.

Ainult see, mida käsus ja lisades päriselt kirjas on. Mida ei ole, seda ei
leiutata — puuduv väli jääb `None`-iks ja reeglimootor näitab selle puudujäägina.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from loe import loe_docx, loe_xlsx


@dataclass
class Sihtmark:
    id: str
    kirjeldus: str
    tuup: str
    aeg: str
    yksus: str
    vahend: str
    markus: str
    allikas: str


@dataclass
class Toke:
    id: str
    asukoht: str
    tuup: str
    valmis: str
    oigus: str
    markus: str
    allikas: str


@dataclass
class Objekt:
    nimi: str
    liik: str
    kaitstud: bool
    meditsiinipunkt: bool
    markus: str
    allikas: str


@dataclass
class Faktid:
    opord_tekst: str
    opord_allikas: str
    sihtmarkid: list[Sihtmark] = field(default_factory=list)
    tokked: list[Toke] = field(default_factory=list)
    objektid: list[Objekt] = field(default_factory=list)
    tsiviilide_arv: int | None = None
    evakuatsiooni_aeg: str | None = None
    evakuatsiooni_koord: str | None = None
    hoiatus: str | None = None
    tuleajad: list[str] = field(default_factory=list)
    reziim: str | None = None
    roe_viide: str | None = None
    tekstid: dict[str, str] = field(default_factory=dict)
    leitud_failid: dict[str, str] = field(default_factory=dict)


def _leia(kaust: Path, muster: str) -> Path | None:
    for p in sorted(kaust.glob(muster)):
        if p.is_file():
            return p
    return None


def _objektid(lisa_j: str, allikas: str) -> list[Objekt]:
    """Loeb CIMIC-lisa „Olulised objektid alas“ rea."""
    objektid: list[Objekt] = []
    for rida in lisa_j.splitlines():
        madal = rida.lower()
        if not any(s in madal for s in ("haigla", "kirik", "sild", "kool", "muuseum")):
            continue
        for osa in re.split(r",\s*", rida):
            osa = osa.strip().rstrip(".")
            if not osa:
                continue
            m = osa.lower()
            if "haigla" in m:
                liik, kaitstud = "haigla", True
            elif "kirik" in m:
                liik, kaitstud = "kirik", True
            elif "sild" in m:
                liik, kaitstud = "sild", False
            elif "kool" in m:
                liik, kaitstud = "kool", True
            elif "muuseum" in m:
                liik, kaitstud = "muuseum", True
            else:
                continue
            objektid.append(
                Objekt(
                    nimi=osa.split("(")[0].strip(),
                    liik=liik,
                    kaitstud=kaitstud,
                    meditsiinipunkt="meditsiinipunkt" in m
                    or "haigla" in m
                    or "meditsiini" in m,
                    markus=osa,
                    allikas=allikas,
                )
            )
    return objektid


def _roll_xlsx(p: Path) -> str | None:
    """Tunne xlsx roll päise järgi (D = sihtmärgid, E = tõkked, G = tagala)."""
    try:
        read = loe_xlsx(p)
    except Exception:
        return None
    if not read:
        return None
    paised = set(read[0])
    if "Sihtmärk" in paised:
        return "D"
    if "Tõke" in paised:
        return "E"
    if "Klass" in paised:
        return "G"
    return None


def _roll_docx(p: Path) -> str | None:
    """Tunne docx roll sisu järgi: OPORD, CIMIC (J) või luure (B)."""
    try:
        tekst = loe_docx(p).lower()
    except Exception:
        return None
    if "lahingukäsk" in tekst or "opord" in tekst:
        return "opord"
    if "cimic" in tekst or "tsiviilmaastik" in tekst:
        return "J"
    if "luure" in tekst:
        return "B"
    return None


def leia_failid(kaust: Path) -> dict[str, Path]:
    """Tunne komplekti failid ära sisu järgi; nimi on ainult varuvariant.

    Nii töötab ka siis, kui kasutaja laadib üles 4 faili omavalitsetud nimedega.
    """
    failid: dict[str, Path] = {}
    for p in sorted(kaust.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".docx":
            roll = _roll_docx(p)
        elif p.suffix.lower() == ".xlsx":
            roll = _roll_xlsx(p)
        else:
            continue
        if roll and roll not in failid:
            failid[roll] = p

    varunimed = {
        "opord": "01_*.docx",
        "D": "Lisa_D*.xlsx",
        "E": "Lisa_E*.xlsx",
        "J": "Lisa_J*.docx",
        "B": "Lisa_B*.docx",
        "G": "Lisa_G*.xlsx",
    }
    for roll, muster in varunimed.items():
        if roll in failid:
            continue
        p = _leia(kaust, muster)
        if p is not None:
            failid[roll] = p
    return failid


def kogu_faktid(kaust: str | Path) -> Faktid:
    kaust = Path(kaust)
    failid = leia_failid(kaust)
    opord_fail = failid.get("opord")
    if opord_fail is None:
        raise FileNotFoundError(
            "OPORD-i .docx ei leitud. Failis peab olema tekst „LAHINGUKÄSK“ "
            "või „OPORD“ — kontrolli, et laadisid OPORD-i, mitte ainult lisad."
        )
    opord_tekst = loe_docx(opord_fail)
    tekstid = {opord_fail.name: opord_tekst}

    f = Faktid(opord_tekst=opord_tekst, opord_allikas=opord_fail.name)

    # Lisa D — sihtmärgid
    d_fail = failid.get("D")
    if d_fail:
        for rida in loe_xlsx(d_fail):
            if not rida.get("Sihtmärk"):
                continue
            f.sihtmarkid.append(
                Sihtmark(
                    id=rida.get("Sihtmärk", ""),
                    kirjeldus=rida.get("Tüüp", ""),
                    tuup=rida.get("Tüüp", ""),
                    aeg=rida.get("Aeg", ""),
                    yksus=rida.get("Üksus", ""),
                    vahend=rida.get("Vahend", ""),
                    markus=rida.get("Märkus", ""),
                    allikas=d_fail.name,
                )
            )
        f.tuleajad = sorted({s.aeg for s in f.sihtmarkid if s.aeg})

    # Lisa E — tõkked
    e_fail = failid.get("E")
    if e_fail:
        for rida in loe_xlsx(e_fail):
            if not rida.get("Tõke"):
                continue
            f.tokked.append(
                Toke(
                    id=rida.get("Tõke", ""),
                    asukoht=rida.get("Asukoht", ""),
                    tuup=rida.get("Tüüp", ""),
                    valmis=rida.get("Valmis", ""),
                    oigus=rida.get("Õigus", ""),
                    markus=rida.get("Märkus", ""),
                    allikas=e_fail.name,
                )
            )

    # Lisa J — objektid, tsiviilid, evakuatsioon, hoiatus
    j_fail = failid.get("J")
    if j_fail:
        lisa_j = loe_docx(j_fail)
        tekstid[j_fail.name] = lisa_j
        f.objektid = _objektid(lisa_j, j_fail.name)

        m = re.search(r"(\d+)\s+elanikku", lisa_j)
        if m:
            f.tsiviilide_arv = int(m.group(1))
        m = re.search(r"[Ee]vakuatsioon algab\s*(H\+\d+(?:[.,]\d+)?)", lisa_j)
        if m:
            f.evakuatsiooni_aeg = m.group(1).replace(",", ".")
        m = re.search(r"kooskõlastab\s+([^.\n]+)", lisa_j)
        if m:
            f.evakuatsiooni_koord = m.group(1).strip()
        for rida in lisa_j.splitlines():
            if "teade elanikele" in rida.lower():
                m = re.search(
                    r"teade elanikele[:\s]*(.+?)(?:\.(?:\s|$)|$)",
                    rida,
                    re.IGNORECASE,
                )
                if m:
                    f.hoiatus = m.group(1).strip()
                break

    # Lisa B — luure (allikaviiteks)
    b_fail = failid.get("B")
    if b_fail:
        tekstid[b_fail.name] = loe_docx(b_fail)

    f.tekstid = tekstid
    f.leitud_failid = {roll: p.name for roll, p in failid.items()}
    f.reziim = tuvasta_reziim(opord_tekst)
    f.roe_viide = tuvasta_roe_viide("\n".join(tekstid.values()))
    return f


def tuvasta_roe_viide(tekst: str) -> str | None:
    """Otsi käsu tekstist viide ROE-kaardile või jõu kasutamise korrale.

    ROE sisu ise on piiratud ega kuulu tsiteerimisele — tööriist märgib ainult,
    kas viide on olemas ja milline see on.
    """
    muster = re.compile(r"\bROE\b|konfliktireegl|jõu kasutamise kor", re.IGNORECASE)
    for rida in (tekst or "").splitlines():
        if muster.search(rida):
            return rida.strip()
    return None


def tuvasta_reziim(tekst: str) -> str | None:
    """OPORD peab ütlema, mis õigusrežiimis tegutsetakse (KKS § 45/48).

    Kui ei ütle, tagastame None — see on ise leid, mitte vaikimisi oletus.
    """
    madal = tekst.lower()
    if "sõjaseisukord" in madal or "sojaseisukord" in madal:
        return "R2"
    if "rahuaja" in madal or "rahuaja" in madal:
        return "R1"
    if "roe" in re.findall(r"\broe\b", madal):
        return "R4"
    return None
