# IHL-i kohustuste register — moodul Käsumeistrile

47 nõuet rahvusvahelisest humanitaarõigusest (AP I art 49, 52, 57 + kultuurivara,
meditsiin, keelatud vahendid), mis on **masinaga kontrollitavad** või märgitud
**inimhinnangu** vajaduseks.

Allikad ja põhjendus: `../IHL_NOUDED.md`, `../OIGUSRAAM.md`.

## Failid

| Fail | Sisu |
|---|---|
| `ihl_nouded.py` | register + `hinda()`, `skaneeri_tekst()`, `vananenud_viited()` |
| `tests/test_ihl_nouded.py` | 10 testi (ootused arvutatud käsitsi) |
| `tests/conftest.py` | lisab `grete/ihl/` süsteemi teele |

## Käivitamine

```bash
cd grete/ihl
python3 -m pytest tests -q
```

## API

```python
from ihl_nouded import hinda, skaneeri_tekst, vananenud_viited, nouded, kokkuvote

leide = hinda(kask)            # struktureeritud käsk (dict) -> list[Leid]
leide = skaneeri_tekst(tekst)  # docx/pdf tekst -> list[Leid] (heuristiline)
nouded()                       # 47 kohustust (register)
vananenud_viited(tekst)        # ["Riigikaitseseadus", "RSKS"] kui viited on aegunud
kokkuvote(leide)               # {"ei vasta": 4, "inimhinnang": 1, ...}
```

Iga `Leid` sisaldab: `id`, `allikas`, `kohustus`, `staatus`, `sonum`, `kohad`.

Staatused:
- `vastab` — nõue on käsu põhjal täidetud,
- `ei vasta` — nõue on täitmata (punane),
- `inimhinnang` — masin ei saa otsustada, inimene peab hindama (kollane),
- `puudub info` — käsk ei ütle selle kohta midagi.

## Struktureeritud käsu kuju

```python
kask = {
    "paastik": "vastase eelüksused joonel T1",     # valikuline
    "tuvastus": {"kriteeriumid": ["soomustehnika"], "tuld_ei_avata": ["tsiviilauto"]},
    "tsiviilkahju_hinnang": {"on": True, "katkestamise_kriteerium": "kui koolibuss teel"},
    "sihtmark": [{
        "nimi": "sild KIVIKÜLA juures",
        "tyyp": "sild",                            # sild/kool/kirik/haigla/talu/elumaja/...
        "sojaline_pohjendus": "kannab rasketehnikat, ümbersõit 40 km",
        "alternatiiv": "blokeerimine kaalutud",
        "hoiatus": "raadio + CIMIC, 2h enne",
        "tsiviile_lahedal": True,
        "tsiviilne": False,
    }],
    "kultuurivara": [{"nimi": "KIVIKÜLA kirik", "kaugus_m": 300, "kasutus": None}],
    "meditsiin": {"evakuatsioonitee": "tee 3", "markeeritud": True},
    "miinid": {"registreeritud": True, "markeeritud": True, "puhastamine": "pioneerirühm"},
    "tsiviilid": {
        "eemaldamine": "CIMIC, 12h enne",
        "positsioonid_tiheasustuses": False,
        "ellujaamisobjektid_ohustatud": False,
    },
    "vangid": {"kord": "S1 kogub, hoitakse TB-1"},
}
```

Puuduv väli = „info puudub", **mitte** „vastab". See on tahtlik: vaikimine ei ole tõend.

## Näidiskäsu tulemus

`../naidiskask/NADISKASK_opord.md` tekstiga:

```
IHL-R08  ei vasta     Tuleülesanne ilma tuvastatud sihtmärgita.
IHL-R10  ei vasta     Tuleülesanne ilma tsiviilkahju hinnanguta.
IHL-R15  inimhinnang  Tekst mainib kultuurivara/pühapaika — kontrolli kaugus ja kasutus.
IHL-R23  ei vasta     Meditsiin on mainitud, aga evakuatsioon on määramata.
IHL-R31  ei vasta     Tekstis on miinid, aga registreerimist/märgistamist ei mainita.
IHL-R45  puudub info  Vangide käsitlemine ei ole tekstis mainitud.
```

## Kuidas Siim selle rakendusse võtab

`siim/app.py` saab importida ilma koodi kopeerimata:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grete" / "ihl"))

from ihl_nouded import skaneeri_tekst, kokkuvote, vananenud_viited
```

Seejärel pärast faili lugemist:

```python
leide = skaneeri_tekst(tekst)
st.metric("IHL-i leiud", f"{kokkuvote(leide)['ei vasta']} punast")
for l in leide:
    st.warning(f"**{l.id}** · {l.allikas} · {l.sonum}")
```

Struktureeritud `hinda()` jaoks on vaja käsu väljad enne kokku panna (WARNO/OPORD
mustandi samm) — see on järgmine integratsioon.

## Piirid (kirjuta ka ekraanile)

- **Ei anna õiguslikku lõpphinnangut.** Ei ütle „seaduslik" ega „sõjakuritegu".
- **Ei ole ammendav.** Mereõigus, õhusõda, okupatsioon ja neutraliteet on väljas.
- **Osalust relvakonventsioonides** (Ottawa, Oslo, CCW protokollid) ei eeldata — kontrolli eraldi.
- `skaneeri_tekst()` on **heuristiline** (märksõnad). Täpne tulemus tuleb `hinda()`-st.
- Iga „ei vasta" ja „inimhinnang" kinnitab **inimene**: komandör või jurist.
