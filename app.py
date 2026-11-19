"""LEGAD agendi demo-leht (Streamlit, port 8091).

Üks töö: lugeda OPORD + lisad ja näidata, millised kohad käsus on
õiguslikult problemaatilised — enne kui käsk välja läheb.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from faktid import kogu_faktid, leia_failid
from lisa import docx_bytes
from reeglid import Leid, hinda

from konfig import NAIDIS

STAATUS = {
    "punane": ("PUNANE", "#b3261e", "#fdecea"),
    "kollane": ("KOLLANE", "#8a6100", "#fff4d6"),
    "roheline": ("ROHELINE", "#1e6b3a", "#e7f4ec"),
}
JARJ = {"punane": 0, "kollane": 1, "roheline": 2}

st.set_page_config(page_title="LEGAD lisa", layout="wide")

st.markdown(
    """
    <style>
      .blokk { border-left: 6px solid #ccc; padding: 10px 14px; margin: 6px 0 14px 0;
               background: #fafafa; border-radius: 4px; }
      .margis { font-size: 12px; font-weight: 700; letter-spacing: .04em;
                padding: 2px 8px; border-radius: 10px; }
      .vaike { color: #555; font-size: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _margis(staatus: str) -> str:
    tekst, varv, taust = STAATUS[staatus]
    return (
        f"<span class='margis' style='color:{varv};background:{taust}'>{tekst}</span>"
    )


def _kuva_leid(l: Leid) -> None:
    with st.expander(f"{l.id} · {l.pealkiri} — {l.staatus.upper()}", expanded=False):
        st.markdown(
            f"{_margis(l.staatus)} &nbsp; <b>{l.pohimote}</b> "
            f"<span class='vaike'>· {l.koht}</span>",
            unsafe_allow_html=True,
        )
        st.write(l.kirjeldus)
        st.caption(
            f"Õiguslik alus: {l.allikas}"
            + (f" · IHL register: {l.ihl_id}" if l.ihl_id else "")
        )
        st.info(f"Soovitus: {l.soovitus}", icon=None)


def _sisendid():
    with st.sidebar:
        st.header("Sisend")
        viis = st.radio(
            "Kust käsk tuleb?",
            ("Näidiskomplekt", "Laadi failid üles"),
            help="Näidiskomplekt on sünteetiline brigaadi OPORD koos lisadega.",
        )
        failid = []
        if viis == "Laadi failid üles":
            failid = st.file_uploader(
                "OPORD ja lisad (.docx, .xlsx)",
                type=["docx", "xlsx"],
                accept_multiple_files=True,
                help="Vaja on OPORD-i .docx ja lisa D, E, J. Failinimed võivad olla samad, mis näidisel.",
            )
            if failid:
                st.caption(
                    f"Valitud {len(failid)} faili: "
                    + ", ".join(x.name for x in failid)
                )
        st.divider()
        koosta = st.button("Koosta LEGAD lisa", type="primary", use_container_width=True)
        st.caption(
            "Sünteetilised andmed. Tööriist ei anna lõplikku õiguslikku hinnangut — "
            "lisa kinnitab LEGAD."
        )
        return viis, failid, koosta


def _laadi(viis: str, failid) -> tuple:
    if viis == "Näidiskomplekt":
        kaust = NAIDIS
    else:
        if not failid:
            raise ValueError(
                "Ühtegi faili ei ole valitud. Vaja on OPORD-i .docx ja lisa D, "
                "E, J (.xlsx/.docx). PDF-e siia laadida ei saa."
            )
        kaust = Path(tempfile.mkdtemp(prefix="legad_"))
        for f in failid:
            (kaust / f.name).write_bytes(f.getbuffer())
        leitud = leia_failid(kaust)
        if "opord" not in leitud:
            nimed = ", ".join(x.name for x in failid) or "—"
            raise ValueError(
                f"OPORD-i ei leitud. Laaditud failid: {nimed}. OPORD-i .docx "
                "peab sisaldama teksti „LAHINGUKÄSK“ või „OPORD“."
            )
    f = kogu_faktid(kaust)
    return f, hinda(f)


def _tulemus(f, leiud: list[Leid]) -> None:
    punased = [l for l in leiud if l.staatus == "punane"]
    kollased = [l for l in leiud if l.staatus == "kollane"]
    rohelised = [l for l in leiud if l.staatus == "roheline"]

    nimes = " · ".join(f"{n}" for n in sorted(f.leitud_failid.values()))
    st.caption(f"Loetud failid ({len(f.leitud_failid)}): {nimes}")
    puuduvad = [
        nimi
        for roll, nimi in (
            ("opord", "OPORD"),
            ("D", "lisa D (sihtmärgid)"),
            ("E", "lisa E (tõkked)"),
            ("J", "lisa J (CIMIC)"),
        )
        if roll not in f.leitud_failid
    ]
    if puuduvad:
        st.warning(
            f"Puuduvad: {', '.join(puuduvad)}. Nende kohta kontrolle ei tehtud — "
            "tulemus on puudulik, mitte „korras“."
        )

    st.subheader("Tulemus")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Punaseid", len(punased), help="Tuleb lahendada enne kinnitamist")
    c2.metric("Kollaseid", len(kollased), help="Vajab LEGAD-i hinnangut")
    c3.metric("Rohelisi", len(rohelised), help="Kontrollitud, kord korras")
    c4.metric("Kontrolle", len(leiud))

    if punased:
        st.error(
            f"{len(punased)} punast leidu: käsk ei ole sellisel kujul kinnitamiseks valmis. "
            "Vaata allpool, mis kohas ja mida muuta."
        )
    elif kollased:
        st.warning("Punaseid leide ei ole. Kollased kohad vajavad LEGAD-i hinnangut.")
    else:
        st.success("Kõik kontrollid läbisid. LEGAD kinnitab lisa.")

    vahekaardid = st.tabs(["Leiud", "Lisa (.docx)", "Allikad"])

    with vahekaardid[0]:
        valik = st.segmented_control(
            "Näita",
            ["Kõik", "Punane", "Kollane", "Roheline"],
            default="Kõik",
        )
        naita = {
            "Kõik": leiud,
            "Punane": punased,
            "Kollane": kollased,
            "Roheline": rohelised,
        }.get(valik or "Kõik", leiud)

        if not naita:
            st.info("Selles vaates leide ei ole.")
        for pohimote in (
            "õiguslik alus",
            "eristamine",
            "proportsionaalsus",
            "sõjaline vajadus",
        ):
            grupp = [l for l in naita if l.pohimote == pohimote]
            if not grupp:
                continue
            st.markdown(f"#### {pohimote.capitalize()}")
            for l in sorted(grupp, key=lambda x: (JARJ[x.staatus], x.id)):
                _kuva_leid(l)

    with vahekaardid[1]:
        st.write(
            "Lisa sisaldab kolme põhimõtte sektsioonid, iga leidu koos käsu koha, "
            "õigusliku aluse ja soovitusega, ning allkirjade plokki."
        )
        st.download_button(
            "Laadi LEGAD lisa alla (.docx)",
            data=docx_bytes(leiud, f),
            file_name="LEGAD_lisa_mustand.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
        with st.expander("Mis on lisa sees?"):
            for pealkiri, _ in (
                ("1. Õiguslik alus ja režiim", ""),
                ("2. Eristamine", ""),
                ("3. Proportsionaalsus", ""),
                ("4. Sõjaline vajadus", ""),
                ("5. Allikad ja katvus", ""),
                ("6. Kinnitused", ""),
            ):
                st.write(f"— {pealkiri}")
            st.caption("Iga leid: staatus, käsu koht, kirjeldus, õiguslik alus, soovitus, kinnitaja.")

    with vahekaardid[2]:
        st.write(f"**OPORD:** {f.opord_allikas}")
        st.write(f"**Režiim käsus:** {f.reziim or 'puudub'}")
        for nimi in f.tekstid:
            st.write(f"— {nimi}")
        with st.expander("OPORD-i tekst"):
            st.text(f.opord_tekst)


def main() -> None:
    st.title("LEGAD lisa — kas käsus on õiguslikult probleemseid kohti?")
    st.markdown(
        "Tööriist loeb OPORD-i ja lisad ning kontrollib **eristamist**, "
        "**proportsionaalsust** ja **sõjalist vajadust**. Probleemsed kohad tulevad "
        "välja enne, kui käsk välja läheb."
    )

    viis, failid, koosta = _sisendid()

    if koosta:
        with st.spinner("Loen käsku ja lisasid, kontrollin kolme põhimõtet…"):
            try:
                st.session_state["tulemus"] = _laadi(viis, failid)
            except Exception as e:  # kasutajale lihtne tekst, mitte traceback
                st.session_state.pop("tulemus", None)
                st.error(f"Käsku ei õnnestunud lugeda: {e}")
                st.info(
                    "Kaks töötavat teed: (1) vali vasakult **Näidiskomplekt** ja "
                    "vajuta uuesti; (2) laadi üles OPORD-i .docx + lisa D, E, J. "
                    "PDF-e ei saa siia laadida."
                )

    if "tulemus" not in st.session_state:
        st.info(
            "Alusta vasakult: vali **Näidiskomplekt** ja vajuta **Koosta LEGAD lisa**. "
            "Tulemuseks on leidude tabel ja allalaaditav .docx."
        )
        return

    f, leiud = st.session_state["tulemus"]
    _tulemus(f, leiud)


main()
