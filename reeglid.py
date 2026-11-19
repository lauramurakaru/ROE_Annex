"""Reeglimootor: faktid -> leiud.

Reeglite metaandmed (pealkiri, nõue, allikas, soovitus) on `reeglid.yaml`-is.
Siin on ainult kontrollid, mis loevad fakte. Tulemus on deterministlik:
sama komplekt annab alati sama leidude nimekirja, ilma AI-ta.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from faktid import Faktid, tuvasta_roe_viide
from materjalid.grete.ihl_nouded import vananenud_viited as _vananenud_viited

REEGLID_FAIL = Path(__file__).with_name("reeglid.yaml")


@dataclass
class Leid:
    id: str
    pealkiri: str
    pohimote: str
    staatus: str  # punane | kollane | roheline
    koht: str
    kirjeldus: str
    allikas: str
    soovitus: str
    kinnitaja: str = "LEGAD"
    ihl_id: str = ""

    @property
    def on_probleem(self) -> bool:
        return self.staatus != "roheline"


def _meta() -> dict[str, dict]:
    with open(REEGLID_FAIL, encoding="utf-8") as f:
        read = yaml.safe_load(f)
    return {r["id"]: r for r in read}


def _leid(meta: dict, id_: str, staatus: str, koht: str, kirjeldus: str) -> Leid:
    m = meta[id_]
    return Leid(
        id=id_,
        pealkiri=m["pealkiri"],
        pohimote=m["pohimote"],
        staatus=staatus,
        koht=koht,
        kirjeldus=kirjeldus,
        allikas=m["allikas"],
        soovitus=m["soovitus"],
        ihl_id=m.get("ihl_id", ""),
    )


def _kogu_tekst(f: Faktid) -> str:
    return "\n".join([f.opord_tekst, *f.tekstid.values()]).lower()


# --- kontrollid ---------------------------------------------------------


def reziim(f: Faktid, m: dict):
    if f.reziim is not None:
        return _leid(
            m, "L01", "roheline", "OPORD",
            f"Käsus on nimetatud režiim {f.reziim}.",
        )
    return _leid(
        m, "L01", "punane", "OPORD 1–5 (režiim puudub)",
        "Käsk ei ütle, kas tegutsetakse sõjaseisukorras (R2), rahuaja jõu "
        "kasutamisel (R1) või rahvusvahelises koostöös (R4). Ilma selleta ei saa "
        "valida, milline proportsionaalsuse test ja kes on pädev otsustaja.",
    )


def vananenud_viited_kaskus(f: Faktid, m: dict):
    leitud = _vananenud_viited(f.opord_tekst)
    if leitud:
        return _leid(
            m, "L02", "kollane", "OPORD",
            f"Käsus on viide kehtetule õigusaktile: {', '.join(leitud)}. "
            "Alates 01.10.2026 kehtib KORKS; Riigikaitseseadus ja RSKS on kehtetud.",
        )
    return _leid(
        m, "L02", "roheline", "OPORD",
        "Vananenud õigusviiteid (Riigikaitseseadus, RSKS) käsus ei ole.",
    )


def roe_viide(f: Faktid, m: dict):
    viide = f.roe_viide or tuvasta_roe_viide(
        "\n".join([f.opord_tekst, *f.tekstid.values()])
    )
    if viide:
        return _leid(
            m, "L03", "roheline", "OPORD",
            f"Käsus on viide ROE-le: „{viide}“. Sisu ja kehtivust kontrollib LEGAD.",
        )
    return _leid(
        m, "L03", "punane", "OPORD 1–5",
        "Käsus ega lisades ei ole viidet kehtivale ROE-kaardile ega jõu kasutamise "
        "korrale. Ilma selleta ei saa hinnata, kas ülesanded on ROE-ga kooskõlas. "
        "ROE sisu on piiratud — tööriist seda ei oleta ega tsiteeri.",
    )


def toke_kultuurivara(f: Faktid, m: dict):
    kirikud = [o for o in f.objektid if o.liik == "kirik"]
    if not kirikud:
        return None
    for t in f.tokked:
        if "kirik" not in t.asukoht.lower():
            continue
        o = kirikud[0]
        med = " ja samas meditsiinipunkt (Lisa G kogunemispunkt)" if o.meditsiinipunkt else ""
        return _leid(
            m, "E01", "punane",
            f"Lisa E / {t.id} ({t.asukoht}); Lisa J / {o.nimi}",
            f"{t.id} „{t.tuup}“ asub {t.asukoht.lower()}. {o.nimi} on kultuurivara"
            f"{med}. Tõke muudab kultuurivara sõjaliseks kasutuseks ja ohustab "
            "meditsiinilist funktsiooni; käsus puudub kaugus ja kirjeldus, kas "
            "tõke on hoones või selle vahetus läheduses.",
        )
    return None


def sihtmarkide_tuvastus(f: Faktid, m: dict):
    if not f.sihtmarkid:
        return _leid(
            m, "E02", "punane", "Lisa D",
            "Käsus ei ole ühtegi sihtmärki, mille tuvastust saaks kontrollida.",
        )
    puudu = [s.id for s in f.sihtmarkid if "tuvastatud" not in s.markus.lower()]
    if not puudu:
        return _leid(
            m, "E02", "roheline", "Lisa D",
            "Kõigil sihtmärkidel on tuvastus kirjas.",
        )
    ootel = [s.id for s in f.sihtmarkid if "kinnitus" in s.markus.lower()]
    lisa = f" {', '.join(ootel)} puhul on märgitud ainult „luure kinnitus“, mis on ootel." if ootel else ""
    return _leid(
        m, "E02", "kollane", f"Lisa D / {', '.join(puudu)}",
        f"Sihtmärgid {', '.join(puudu)} on loetletud tüübi ja ajaga, kuid ilma "
        "tuvastuskriteeriumi, tuvastusallika ja tuvastusajata." + lisa,
    )


def lohkamine_taristu(f: Faktid, m: dict):
    sillad = [o for o in f.objektid if o.liik == "sild"]
    for t in f.tokked:
        if "lõhke" not in t.tuup.lower() and "lõhkamine" not in t.tuup.lower():
            continue
        if "maantee" not in t.asukoht.lower():
            continue
        sild = f" Lisa J järgi on {sillad[0].nimi.lower()} elutähtis taristu." if sillad else ""
        return _leid(
            m, "E03", "kollane", f"Lisa E / {t.id} ({t.asukoht})",
            f"{t.id} sisaldab lõhkekohti maanteel nr 3. Käsus ei ole hinnatud, kas "
            f"lõhkamine tabab tsiviiltaristut ja kas tee või sild on praegu sõjaline objekt.{sild}",
        )
    return None


def tsiviilkahju_hinnang(f: Faktid, m: dict):
    if not f.tsiviilide_arv or not f.tuleajad:
        return None
    tekst = _kogu_tekst(f)
    if "tsiviilkahju" in tekst or "cde" in tekst:
        return _leid(
            m, "P01", "roheline", "OPORD / Lisa D",
            "Tsiviilkahju hinnang on käsus olemas.",
        )
    return _leid(
        m, "P01", "kollane", f"Lisa D ({f.tuleajad[0]}–{f.tuleajad[-1]}); Lisa J",
        f"{f.tsiviilide_arv} tsiviilelanikku on JÕHVI põhjaosas. Tulelöögid algavad "
        f"{f.tuleajad[0]} ja kestavad {f.tuleajad[-1]}, kuid käsus puudub "
        "tsiviilkahju hinnang ja otsus, et oodatav kahju ei ole ülemäärane.",
    )


def evakuatsiooni_lopp(f: Faktid, m: dict):
    if not f.evakuatsiooni_aeg:
        return None
    tekst = _kogu_tekst(f)
    if "evakuatsiooni lõpp" in tekst or "evakuatsioon lõpeb" in tekst:
        return _leid(
            m, "P02", "roheline", "OPORD 3d; Lisa J",
            "Evakuatsiooni lõpp on käsus kirjas.",
        )
    first = f.tuleajad[0] if f.tuleajad else "esimene tulelöök"
    return _leid(
        m, "P02", "kollane", "OPORD 3d; Lisa J",
        f"Evakuatsioon algab {f.evakuatsiooni_aeg}, kuid käsus ei ole evakuatsiooni "
        f"lõppu ega kinnitust, et tsiviilid on alalt lahkunud. Esimene tulelöök on {first}.",
    )


def hoiatuse_kanal(f: Faktid, m: dict):
    if not f.hoiatus:
        return _leid(
            m, "P03", "punane", "OPORD 3d; Lisa J",
            "Käsus ei ole tsiviilelanike hoiatust.",
        )
    kanalid = ("raadio", "sms", "cimic", "päästeamet", "sõiduk", "kõlar", "meedia")
    if any(k in f.hoiatus.lower() for k in kanalid):
        return _leid(
            m, "P03", "roheline", "Lisa J",
            f"Hoiatusel on kanal: {f.hoiatus}",
        )
    return _leid(
        m, "P03", "kollane", "Lisa J / infooperatsioon",
        f"Hoiatus on sõnastatud („{f.hoiatus}“), kuid puudub kanal (raadio, SMS, "
        "CIMIC, sõidukid), saatja ja kordus. Art 57(2)(c) nõuab efektiivset hoiatust.",
    )


def katkestamine(f: Faktid, m: dict):
    if "katkest" in _kogu_tekst(f):
        return _leid(
            m, "P05", "roheline", "OPORD",
            "Katkestamise kriteerium on käsus olemas.",
        )
    return _leid(
        m, "P05", "kollane", "OPORD 3d/5",
        "Käsus puudub katkestamise kriteerium ja volitus: kes ja mille alusel "
        "peatab tulelöögi, kui selgub, et objekt ei ole sõjaline või kahju "
        "muutub ülemääraseks.",
    )


def tokke_eesmark(f: Faktid, m: dict):
    for t in f.tokked:
        if "lõhke" not in t.tuup.lower() and "miin" not in t.tuup.lower():
            continue
        if any(s in t.markus.lower() for s in ("katab", "eesmärk", "takistab", "peata")):
            continue
        return _leid(
            m, "V01", "kollane", f"Lisa E / {t.id}",
            f"{t.id} ({t.tuup}) eesmärk on kirjeldamata: kas tõke peatab vastase "
            "liikumise, kaitseb positsiooni või hävitab taristu? Alternatiive "
            "(blokeerimine, rajatis) ei ole kaalutud.",
        )
    return None


def sihtmargi_eesmark(f: Faktid, m: dict):
    seotud = [s for s in f.sihtmarkid if "katab" in s.markus.lower()]
    if not seotud:
        return None
    s = seotud[0]
    return _leid(
        m, "V02", "roheline", f"Lisa D / {s.id}",
        f"{s.id} eesmärk on seotud konkreetse manöövriga („{s.markus}“) — "
        "sõjaline vajadus on jälgitav.",
    )


def evakuatsioon_korraldatud(f: Faktid, m: dict):
    if not f.evakuatsiooni_aeg or not f.tsiviilide_arv:
        return None
    koord = f" Kooskõlastab {f.evakuatsiooni_koord}." if f.evakuatsiooni_koord else ""
    return _leid(
        m, "V06", "roheline", "OPORD 3d; Lisa J",
        f"Tsiviilide evakuatsioon on korraldatud: {f.tsiviilide_arv} elanikku, "
        f"algus {f.evakuatsiooni_aeg}.{koord} See on kaitseja art 58(a) esimene samm.",
    )


def roe_piirang(f: Faktid, m: dict):
    viide = f.roe_viide or tuvasta_roe_viide(
        "\n".join([f.opord_tekst, *f.tekstid.values()])
    )
    if not viide:
        return None
    madal = viide.lower()
    if not any(
        s in madal
        for s in ("ainult enesekaitse", "enesekaitse", "keelatud", "piiratud", "ei tohi")
    ):
        return None
    return _leid(
        m, "L04", "kollane", "OPORD / ROE viide",
        f"ROE ütleb: „{viide}“. See on käskija poliitika, mitte IHL-i nõue. "
        "Seadus võib lubada rohkem, kuid käsk piirab. Vastupidine juhtum — ROE lubab "
        "IHL-iga vastuolus olevat tegevust — tuleb täitmata jätta ja teatada (KKS § 44 lg 4–5).",
    )


# --- mootor -------------------------------------------------------------


def hinda(f: Faktid) -> list[Leid]:
    meta = _meta()
    tulemused: list[Leid] = []
    for id_, m in meta.items():
        fn = globals()[m["kontroll"]]
        tulemus = fn(f, meta)
        if tulemus is None:
            continue
        if isinstance(tulemus, list):
            tulemused.extend(tulemus)
        else:
            tulemused.append(tulemus)
    return tulemused
