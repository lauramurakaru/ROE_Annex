"""IHL-i kohustuste register ja kontrollid Käsumeistri jaoks.

Allikas: AP I art 49, 52, 57 + kultuurivara, meditsiin, keelatud vahendid.
Iga nõue: ID, allikas, kohustus, tüüp (M = masin, I = inimene).

Moodul EI anna õiguslikku lõpphinnangut. Ta toob välja koha, allika ja selle,
kes peab kinnitama.

Kasutus:
    from ihl_nouded import hinda, skaneeri_tekst, vananenud_viited
    for leid in hinda(kask_dict):
        print(leid.id, leid.staatus, leid.sonum)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

STAATUS_VASTAB = "vastab"
STAATUS_EI_VASTA = "ei vasta"
STAATUS_INIMHINNANG = "inimhinnang"
STAATUS_PUUDUB = "puudub info"

# Objektid, mis tavaliselt on tsiviilkasutuses (AP I art 52 lg 3 eeldus).
EELDUS_TSIVIIL = {"sild", "kool", "kirik", "haigla", "talu", "elumaja", "veehaare", "tehas"}

# Registri read: (id, allikas, kohustus, tyyp, vali)
_REGISTER: tuple[tuple[str, str, str, str, str], ...] = (
    # --- AP I art 49: rünnaku mõiste ---
    ("IHL-R01", "AP I art 49 lg 1", "Rünnak on vägivald vastase vastu nii pealetungil kui kaitsel.", "M", "tegevused"),
    ("IHL-R02", "AP I art 49 lg 2-3", "Nõuded kehtivad kõigile rünnakutele, mis mõjutavad tsiviile maismaal.", "M", "sihtmargid"),
    ("IHL-R03", "AP I art 49 lg 1", "Kaitsepositsioonilt avatud tuli on rünnak, mitte erand.", "I", "tegevused"),
    # --- AP I art 52: tsiviilobjektid ---
    ("IHL-R04", "AP I art 52 lg 1", "Tsiviilobjekte ei tohi rünnata.", "M", "sihtmargid"),
    ("IHL-R05", "AP I art 52 lg 2", "Objekt on sõjaline ainult tõhusa panuse JA konkreetse eelise korral.", "I", "sihtmargid"),
    ("IHL-R06", "AP I art 52 lg 3", "Kahtluse korral eeldatakse, et objekt on tsiviilne.", "I", "sihtmargid"),
    # --- AP I art 57: ettevaatusabinõud ---
    ("IHL-R07", "AP I art 57 lg 1", "Pidev hool tsiviilelanikkonna säästmiseks.", "M", "tsiviilid"),
    ("IHL-R08", "AP I art 57 lg 2(a)(i)", "Kontrolli, et sihtmärk on sõjaline objekt.", "M", "tuvastus"),
    ("IHL-R09", "AP I art 57 lg 2(a)(ii)", "Vali vahend ja meetod, mis tekitab vähimat tsiviilkahju.", "I", "sihtmargid"),
    ("IHL-R10", "AP I art 57 lg 2(a)(iii)", "Ära ründa, kui oodatav tsiviilkahju on ülemäärane.", "I", "tsiviilkahju_hinnang"),
    ("IHL-R11", "AP I art 57 lg 2(b)", "Tühista või peata rünnak, kui tingimused muutuvad.", "M", "tsiviilkahju_hinnang"),
    ("IHL-R12", "AP I art 57 lg 2(c)", "Anna efektiivne eelhoiatus tsiviilelanikkonnale.", "M", "hoiatus"),
    ("IHL-R13", "AP I art 57 lg 3", "Vali sihtmärkide hulgast see, mis ohustab tsiviile kõige vähem.", "I", "sihtmargid"),
    ("IHL-R14", "AP I art 57 lg 5", "Artikkel ei luba rünnata tsiviile ka heade kavatsuste korral.", "M", "sihtmargid"),
    # --- Kultuurivara ---
    ("IHL-R15", "AP I art 53", "Keelatud vaenulikud aktid kultuurivara vastu, selle sõjaline kasutus ja repressaalid.", "I", "kultuurivara"),
    ("IHL-R16", "AP I art 53 + 1954 Haagi konv. art 4", "Erand ainult imperatiivse sõjalise vajaduse korral, mitte laialt.", "I", "kultuurivara"),
    ("IHL-R17", "1954 teine protokoll (1999)", "Kultuurivara tõhustatud kaitse; sõjalisi objekte ei paigutata selle lähedale.", "I", "kultuurivara"),
    ("IHL-R18", "CIHL reeglid 38-41", "Kultuurivara ja pühapaikade kaitse ka tavaõiguse järgi.", "I", "kultuurivara"),
    ("IHL-R19", "Rooma statuut art 8(2)(b)(ix)", "Kultuuri-, haridus- ja usuobjektide ning haiglate ründamine on sõjakuritegu.", "I", "kultuurivara"),
    # --- Meditsiin ---
    ("IHL-R20", "AP I art 12", "Meditsiiniüksusi ei tohi rünnata.", "M", "meditsiin"),
    ("IHL-R21", "AP I art 13", "Kaitse kaob ainult vaenuliku kasutuse korral ja hoiatusega.", "I", "meditsiin"),
    ("IHL-R22", "AP I art 21-24", "Meditsiinitransport kaitstud, kui äratuntav ja mitte kuritarvitatud.", "M", "meditsiin"),
    ("IHL-R23", "GC I art 15", "Haavatuid hooldatakse ja evakueeritakse viivitamata.", "M", "meditsiin"),
    ("IHL-R24", "AP I art 10", "Haavatute kaitse ja hooldus ilma vahetegemiseta.", "M", "meditsiin"),
    # --- Keelatud vahendid ja meetodid ---
    ("IHL-R25", "AP I art 35 lg 1", "Sõjapidamise meetodite valik ei ole piiramatu.", "M", "relvad"),
    ("IHL-R26", "AP I art 35 lg 2", "Keelatud ülemäärast vigastust või tarbetut kannatust tekitavad vahendid.", "M", "relvad"),
    ("IHL-R27", "AP I art 35 lg 3", "Keelatud laiamastaabiline, pikaajaline raske keskkonnakahju.", "M", "relvad"),
    ("IHL-R28", "AP I art 36", "Uus relv tuleb enne kasutuselevõttu õiguslikult hinnata.", "M", "relvad"),
    ("IHL-R29", "AP I art 51 lg 4", "Valimatu rünnak on keelatud.", "M", "relvad"),
    ("IHL-R30", "CCW protokoll I", "Keelatud mittetuvastatavad killud.", "M", "relvad"),
    ("IHL-R31", "CCW muudetud II protokoll art 3-5", "Miinid: kasutuspiirangud, registreerimine, märgistamine, puhastamine.", "M", "miinid"),
    ("IHL-R32", "CCW protokoll III", "Süütavad relvad: piirangud tsiviilide lähedal ja taimestiku vastu.", "M", "relvad"),
    ("IHL-R33", "CCW protokoll IV", "Keelatud pimedaks tegevad laserid.", "M", "relvad"),
    ("IHL-R34", "Keemiarelvade konventsioon (1993)", "Keelatud keemiarelvad ja nende kasutamine.", "M", "relvad"),
    ("IHL-R35", "Bioloogiliste relvade konventsioon (1972)", "Keelatud bioloogilised relvad.", "M", "relvad"),
    ("IHL-R36", "ENMOD (1976)", "Keelatud keskkonna muutmine vaenulikul eesmärgil.", "M", "relvad"),
    # --- Tsiviilide kaitse ja kaitseja kohustused ---
    ("IHL-R37", "AP I art 51 lg 2", "Tsiviilelanikkonda ei tohi rünnata ega sellega ähvardada.", "M", "tsiviilid"),
    ("IHL-R38", "AP I art 51 lg 3", "Otse vaenutegevuses osalev tsiviil kaotab kaitse selleks ajaks.", "I", "tsiviilid"),
    ("IHL-R39", "AP I art 51 lg 7", "Inimkilpide kasutamine keelatud; see ei vabasta ründajat kohustustest.", "I", "tsiviilid"),
    ("IHL-R40", "AP I art 58(a)", "Kaitseja eemaldab tsiviilid sõjaliste objektide lähedusest.", "M", "tsiviilid"),
    ("IHL-R41", "AP I art 58(b)", "Kaitseja ei paiguta sõjalisi objekte tiheasustusse.", "M", "tsiviilid"),
    ("IHL-R42", "AP I art 54", "Keelatud rünnata ellujäämiseks hädavajalikke objekte.", "M", "tsiviilid"),
    ("IHL-R43", "AP I art 55-56", "Keskkond ja ohtlikud objektid (tamm, tuumajaam) erikaitse all.", "I", "tsiviilid"),
    ("IHL-R44", "AP I art 56 lg 1", "Ohtlikke jõude sisaldavat objekti ei rünnata, kui oht massiliseks tsiviilohvriks.", "I", "tsiviilid"),
    # --- Vangid ---
    ("IHL-R45", "GC III", "Vangide kohtlemine, registreerimine ja kaitse korraldatud.", "M", "vangid"),
    ("IHL-R46", "GC IV", "Kinnipeetud tsiviilisikute kaitse.", "M", "vangid"),
    ("IHL-R47", "AP I art 75", "Üldised tagatised kõigile kaitstud isikutele.", "M", "vangid"),
)

NOUDED: tuple[dict[str, str], ...] = tuple(
    {"id": i, "allikas": a, "kohustus": k, "tyyp": t, "vali": v}
    for i, a, k, t, v in _REGISTER
)
_REG = {n["id"]: n for n in NOUDED}

# Vananenud viited: 01.10.2026 kehtib KORKS, RiKS on kehtetu.
_VANANENUD = (
    (re.compile(r"riigikaitseseadus", re.I), "Riigikaitseseadus"),
    (re.compile(r"\bRSKS\b|rahvusvahelise sõjalise koostöö seadus", re.I), "RSKS"),
)


@dataclass(frozen=True)
class Leid:
    """Üks kontrolli tulemus. `kohad` viitab käsu lõikudele, kui need on teada."""

    id: str
    allikas: str
    kohustus: str
    staatus: str
    sonum: str
    kohad: tuple[str, ...] = ()


def nouded() -> list[dict[str, str]]:
    """Tagasta kohustuste register (koopia, mida kutsuja võib muuta)."""
    return [dict(n) for n in NOUDED]


def _leid(id_: str, staatus: str, sonum: str, kohad: tuple[str, ...] = ()) -> Leid:
    n = _REG[id_]
    return Leid(
        id=id_,
        allikas=n["allikas"],
        kohustus=n["kohustus"],
        staatus=staatus,
        sonum=sonum,
        kohad=kohad,
    )


def _tyhi(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return not v.strip()
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) == 0
    return False


def hinda(kask: dict[str, Any]) -> list[Leid]:
    """Hinda struktureeritud käsku IHL-i kohustuste vastu.

    `kask` on lihtne dict (vt README). Puuduv väli tähendab „info puudub",
    mitte „vastab". Tulemus on sorditud ID järgi.
    """
    if not isinstance(kask, dict):
        raise TypeError("kask peab olema dict")
    leide: list[Leid] = []

    # R01: päästik (trigger) on rünnak ja nõuab tuvastust
    if "paastik" in kask and not _tyhi(kask.get("paastik")):
        tuvastus = kask.get("tuvastus") or {}
        if _tyhi(tuvastus.get("kriteeriumid")):
            leide.append(_leid("IHL-R01", STAATUS_EI_VASTA,
                               "Päästikuga tuleülesanne ilma tuvastuskriteeriumiteta.", ("paastik",)))
        else:
            leide.append(_leid("IHL-R01", STAATUS_VASTAB,
                               "Päästik on seotud tuvastuskriteeriumitega.", ("paastik",)))

    # R08: tuvastus (alati kontrollitav)
    tuvastus = kask.get("tuvastus") or {}
    if _tyhi(tuvastus.get("kriteeriumid")):
        leide.append(_leid("IHL-R08", STAATUS_EI_VASTA, "Tuvastuskriteeriumid puuduvad."))
    else:
        leide.append(_leid("IHL-R08", STAATUS_VASTAB, "Tuvastuskriteeriumid on antud."))

    # Sihtmärgipõhised nõuded
    for i, t in enumerate(kask.get("sihtmark") or []):
        if not isinstance(t, dict):
            continue
        koht = (t.get("nimi") or f"sihtmärk #{i + 1}",)
        pohj = (t.get("sojaline_pohjendus") or "").strip()
        tyyp = (t.get("tyyp") or "").lower()

        if t.get("tsiviilne"):
            leide.append(_leid("IHL-R04", STAATUS_EI_VASTA,
                               f"'{koht[0]}' on märgitud tsiviilobjektiks, aga on sihtmärkide seas.", koht))

        if not pohj:
            leide.append(_leid("IHL-R05", STAATUS_EI_VASTA,
                               f"'{koht[0]}' sõjalise objekti põhjendus puudub (art 52 lg 2).", koht))
        else:
            leide.append(_leid("IHL-R05", STAATUS_VASTAB,
                               f"'{koht[0]}' sõjaline põhjendus on antud.", koht))

        if tyyp in EELDUS_TSIVIIL:
            if pohj:
                leide.append(_leid("IHL-R06", STAATUS_VASTAB,
                                   f"'{koht[0]}' puhul on tõend sõjalise kasutuse kohta.", koht))
            else:
                leide.append(_leid("IHL-R06", STAATUS_INIMHINNANG,
                                   f"'{koht[0]}' on tavaliselt tsiviilkasutuses: eeldatakse tsiviilne.", koht))

        if _tyhi(t.get("alternatiiv")):
            leide.append(_leid("IHL-R09", STAATUS_INIMHINNANG,
                               f"'{koht[0]}' puhul ei ole alternatiivset vahendit kaalutud.", koht))
        else:
            leide.append(_leid("IHL-R09", STAATUS_VASTAB,
                               f"'{koht[0]}' puhul on alternatiivi kaalutud.", koht))

        if t.get("tsiviile_lahedal"):
            if _tyhi(t.get("hoiatus")):
                leide.append(_leid("IHL-R12", STAATUS_EI_VASTA,
                                   f"'{koht[0]}' on tsiviilide lähedal, aga hoiatust ei ole.", koht))
            else:
                leide.append(_leid("IHL-R12", STAATUS_VASTAB,
                                   f"'{koht[0]}' kohta on hoiatus antud.", koht))

    # R10 / R11: tsiviilkahju hinnang ja katkestamine
    hinnang = kask.get("tsiviilkahju_hinnang") or {}
    if hinnang.get("on"):
        leide.append(_leid("IHL-R10", STAATUS_VASTAB, "Tsiviilkahju hinnang on olemas."))
    else:
        leide.append(_leid("IHL-R10", STAATUS_EI_VASTA, "Tsiviilkahju hinnang (CDE) puudub."))

    if _tyhi(hinnang.get("katkestamise_kriteerium")):
        leide.append(_leid("IHL-R11", STAATUS_EI_VASTA, "Katkestamise kriteerium puudub."))
    else:
        leide.append(_leid("IHL-R11", STAATUS_VASTAB, "Katkestamise kriteerium on antud."))

    # Kultuurivara
    for i, k in enumerate(kask.get("kultuurivara") or []):
        nimi = (k.get("nimi") if isinstance(k, dict) else str(k)) or f"kultuurivara #{i + 1}"
        kaugus = k.get("kaugus_m") if isinstance(k, dict) else None
        kasutus = k.get("kasutus") if isinstance(k, dict) else None
        if kaugus is None:
            sonum = f"'{nimi}' kaugus positsioonidest puudub."
            if kasutus:
                sonum += f" Kasutus: {kasutus}."
            leide.append(_leid("IHL-R15", STAATUS_INIMHINNANG, sonum, (nimi,)))
        elif kasutus:
            leide.append(_leid("IHL-R15", STAATUS_EI_VASTA,
                               f"'{nimi}' kasutatakse sõjalisel otstarbel ({kasutus}).", (nimi,)))
        else:
            leide.append(_leid("IHL-R15", STAATUS_VASTAB,
                               f"'{nimi}' on {kaugus} m kaugusel ega ole sõjalises kasutuses.", (nimi,)))

    # Meditsiin: evakuatsioon on kohustus ka siis, kui plaan puudub täielikult
    med = kask.get("meditsiin") or {}
    if _tyhi(med.get("evakuatsioonitee")):
        leide.append(_leid("IHL-R23", STAATUS_EI_VASTA, "Meditsiini evakuatsioonitee on määramata."))
    else:
        leide.append(_leid("IHL-R23", STAATUS_VASTAB, "Meditsiini evakuatsioonitee on määratud."))

    if "meditsiin" in kask:
        if med.get("markeeritud"):
            leide.append(_leid("IHL-R22", STAATUS_VASTAB, "Meditsiinitransport on märgistatud."))
        else:
            leide.append(_leid("IHL-R22", STAATUS_INIMHINNANG,
                               "Meditsiinitranspordi märgistus ja kaitse on kontrollimata."))

    # Miinid
    if "miinid" in kask:
        m = kask.get("miinid") or {}
        puudu = []
        if not m.get("registreeritud"):
            puudu.append("registreerimata")
        if not m.get("markeeritud"):
            puudu.append("märgistamata")
        if _tyhi(m.get("puhastamine")):
            puudu.append("puhastamata")
        if puudu:
            leide.append(_leid("IHL-R31", STAATUS_EI_VASTA,
                               "Miinid on " + ", ".join(puudu) + " (CCW II protokoll art 4-5)."))
        else:
            leide.append(_leid("IHL-R31", STAATUS_VASTAB,
                               "Miinid on registreeritud, märgistatud ja puhastamine korraldatud."))

    # Tsiviilid (kaitseja kohustused)
    ts = kask.get("tsiviilid") or {}
    if _tyhi(ts.get("eemaldamine")):
        leide.append(_leid("IHL-R40", STAATUS_EI_VASTA, "Tsiviilide eemaldamine on korraldamata (art 58(a))."))
    else:
        leide.append(_leid("IHL-R40", STAATUS_VASTAB, "Tsiviilide eemaldamine on korraldatud."))

    if "positsioonid_tiheasustuses" in ts:
        if ts.get("positsioonid_tiheasustuses"):
            leide.append(_leid("IHL-R41", STAATUS_EI_VASTA,
                               "Sõjalised objektid on paigutatud tiheasustusse (art 58(b))."))
        else:
            leide.append(_leid("IHL-R41", STAATUS_VASTAB, "Sõjalisi objekte ei ole paigutatud tiheasustusse."))

    if "ellujaamisobjektid_ohustatud" in ts:
        if ts.get("ellujaamisobjektid_ohustatud"):
            leide.append(_leid("IHL-R42", STAATUS_EI_VASTA,
                               "Ellujäämiseks hädavajalikud objektid on ohustatud (art 54)."))
        else:
            leide.append(_leid("IHL-R42", STAATUS_VASTAB, "Ellujäämisobjekte ei ohustata."))

    # Vangid
    if _tyhi((kask.get("vangid") or {}).get("kord")):
        leide.append(_leid("IHL-R45", STAATUS_EI_VASTA, "Vangide käsitlemise kord puudub (GC III)."))
    else:
        leide.append(_leid("IHL-R45", STAATUS_VASTAB, "Vangide käsitlemise kord on antud."))

    return sorted(leide, key=lambda l: l.id)


def skaneeri_tekst(tekst: str) -> list[Leid]:
    """Heuristiline skanner käsu tekstile (docx/pdf tekst).

    Leiab ainult seda, mida saab märksõnadega tuvastada. Täpsem hinnang on `hinda()`.
    """
    t = (tekst or "").lower()
    leide: list[Leid] = []

    miinid = "miin" in t
    miinid_registris = bool(
        re.search(r"miin\w*[^.\n]{0,120}(register|registreerim\w*|registreeritud)", t)
    )
    if miinid and not miinid_registris:
        leide.append(_leid("IHL-R31", STAATUS_EI_VASTA,
                           "Tekstis on miinid, aga registreerimist/märgistamist ei mainita."))

    if "kirik" in t or "kultuurivara" in t:
        leide.append(_leid("IHL-R15", STAATUS_INIMHINNANG,
                           "Tekst mainib kultuurivara/pühapaika — kontrolli kaugus ja kasutus."))

    runnak = re.search(r"(avada tuli|avaneb tuli|tuld avaneb|tuld avada|avada kaudtuli|kaudtuli)", t)
    if runnak:
        if "tuvastatud" not in t:
            leide.append(_leid("IHL-R08", STAATUS_EI_VASTA,
                               "Tuleülesanne ilma tuvastatud sihtmärgita."))
        if "tsiviilkahju" not in t and "proportsionaal" not in t:
            leide.append(_leid("IHL-R10", STAATUS_EI_VASTA,
                               "Tuleülesanne ilma tsiviilkahju hinnanguta."))

    if "tsiviil" in t and "hoiat" not in t:
        leide.append(_leid("IHL-R12", STAATUS_EI_VASTA,
                           "Tsiviile mainitakse, aga eelhoiatust ei ole."))

    if "meditsiin" in t and "evakuu" not in t:
        leide.append(_leid("IHL-R23", STAATUS_EI_VASTA,
                           "Meditsiin on mainitud, aga evakuatsioon on määramata."))

    if len(t) > 200 and "vang" not in t:
        leide.append(_leid("IHL-R45", STAATUS_PUUDUB,
                           "Vangide käsitlemine ei ole tekstis mainitud."))

    return sorted(leide, key=lambda l: l.id)


def vananenud_viited(tekst: str) -> list[str]:
    """Tagasta tekstis leitud vananenud õigusaktide nimed (RiKS, RSKS).

    Alates 01.10.2026 kehtib KORKS; Riigikaitseseadus on kehtetu.
    """
    leitud = set()
    for muster, nimi in _VANANENUD:
        if muster.search(tekst or ""):
            leitud.add(nimi)
    return sorted(leitud)


def kokkuvote(leide: list[Leid]) -> dict[str, int]:
    """Loenda leiud staatuse kaupa (demo-ekraani jaoks)."""
    loend = {STAATUS_EI_VASTA: 0, STAATUS_INIMHINNANG: 0, STAATUS_PUUDUB: 0, STAATUS_VASTAB: 0}
    for l in leide:
        loend[l.staatus] = loend.get(l.staatus, 0) + 1
    return loend
