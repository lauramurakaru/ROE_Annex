"""LEGAD lisa allikad ja katvus.

Otsus: ROE-kihi ainus allikas on **Sanremo ROE Handbook (2009)**.
Ülejäänud kolm andmetes olevat PDF-i (LOAC manual, NATO ROE monograafia,
Operational Law Handbook) jäävad kasutamata — neid ei tsiteerita ega viidata.

IHL-põhi ja Eesti õigus tulevad Grete registrist / õigusraamist.
"""
from __future__ import annotations

ALLIKAD: list[dict[str, str]] = [
    {
        "nimi": "IHL: AP I, GC I–IV, CCW",
        "viide": "Grete register IHL-R01…R47",
        "mida": "Eristamine, proportsionaalsus, sõjaline vajadus, kultuurivara, meditsiin.",
    },
    {
        "nimi": "Eesti õigus: KKS § 44–49, KORKS § 40, PS § 123",
        "viide": "grete/OIGUSRAAM.md",
        "mida": "Režiim, pädevus, ROE ja seaduse piir, vananenud viited.",
    },
    {
        "nimi": "Sanremo ROE Handbook (IIHL, 2009)",
        "viide": "ptk II–VI; Annex A lisa 6 „Targeting and ROE“ (lk 26); Annex C lisa 1 „ROE Annex to OPORDER“ (lk 64)",
        "mida": "ROE on piirang, mis ei tohi ületada seadust; ROE lisa struktuur ja sõnastus.",
    },
]

# Teadlikult katmata — nimetatud, et puudujääk ei jääks märkamata.
EI_KASITA: list[str] = [
    "üksuse kehtiv piiratud ROE-kaart (tööriist ainult viitab, ei tsiteeri)",
    "liitlaste ja organisatsioonide ROE erisused",
    "operatsiooniõiguse muud teemad: vangid, tsiviilnõuded, keskkond, lepingud",
]
