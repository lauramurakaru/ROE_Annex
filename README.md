# LEGAD agent — OPORD-i õiguslisa

Tööriist, mis loeb OPORD-i ja selle lisad ning toob **planeerimise faasis** välja
kohad, mis ei ole õiguslikult korras. Kontrollitakse kolme põhimõtet:

- **eristamine** (distinction) — kas iga sihtmärk/tõke on sõjaline objekt ja kas
  tsiviilobjektid, kultuurivara ja meditsiin on puutumata;
- **proportsionaalsus** (proportionality) — kas tsiviilkahju hinnang, evakuatsiooni
  lõpp, efektiivne hoiatus ja katkestamise kriteerium on käsus;
- **sõjaline vajadus** (military necessity) — kas igal tegevusel on eesmärk ja kas
  alternatiive on kaalutud.

Tulemus: leidude tabel (punane/kollane/roheline) ja allalaaditav **LEGAD lisa
.docx** mustand. Lõpliku hinnangu annab ja lisa kinnitab **LEGAD**, mitte tööriist.

## Käivitamine

```bash
cd ~/legad-github
pip install -r requirements.txt
streamlit run app.py --server.port 8091
```

Ava masina Firefoxis **http://localhost:8091**.

Vasakult: vali **Näidiskomplekt** → **Koosta LEGAD lisa**.

## Sisend

Demo kasutab sünteetilist brigaadi käsku:
`naidis/brigaadi_kask/`

| Fail | Mida sealt loetakse |
|---|---|
| `01_Brigaadi_OPORD_1JVP.docx` | käsu tekst, režiim |
| `Lisa_D_tuletoetus.xlsx` | sihtmärgid, ajad, vahendid |
| `Lisa_E_pioneer.xlsx` | tõkked, asukohad, õigused |
| `Lisa_J_CIMIC.docx` | objektid, tsiviilid, evakuatsioon, hoiatus |
| `Lisa_B_luure.docx` | allikaviide |

Failid tuntakse ära **sisu** järgi (OPORD = tekst „LAHINGUKÄSK/OPORD“,
lisa D = veerg „Sihtmärk“, lisa E = veerg „Tõke“, lisa J = „CIMIC“),
seega failinimed võivad olla ka teised. Demo jaoks piisab 4 failist:
OPORD + lisa D + lisa E + lisa J.

## Materjalid

`materjalid/grete/` sisaldab IHL-registri ja õigusraami hetkeseisu
(`IHL_NOUDED.md`, `OIGUSRAAM.md`, `ihl_nouded.py`).

`reeglid.yaml` iga reegel viitab registri nõudele (`IHL-R01…R47`), nii on
õiguslik alus jälgitav kuni algallikani. Test kontrollib, et ükski viide ei
osuta olematule nõudele.

## Kuidas see töötab

```
docx/xlsx  →  faktid.py   (ainult see, mis on kirjas)
           →  reeglid.py  (13 deterministlikku kontrolli, reeglid.yaml)
           →  lisa.py     (.docx: 3 põhimõtet + leiud + allkirjad)
           →  app.py      (Streamlit, port 8091)
```

- **Faktid** on deterministlikud: sama komplekt annab alati sama tulemuse.
- **Iga leid** sisaldab käsu kohta, kirjeldust, õiguslikku alust (nt AP I art 53)
  ja soovitust.
- **Puuduv info** on ise leid (kollane/punane), mitte vaikimine.
- AI-d ei kasutata; `reeglid.yaml` on mõeldud eksperdile muutmiseks.

## Näidisleiud

| ID | Leid | Staatus |
|---|---|---|
| L01 | Käsus ei ole nimetatud õigusrežiimi (KKS § 45/48) | punane |
| L02 | Viide kehtetule aktile (RiKS/RSKS) | roheline |
| L03 | ROE-kaart või jõu kasutamise kord on tuvastamata | punane |
| L04 | ROE piirang on käskija poliitika, mitte seadus | kollane* |
| E01 | T3 tõke SAARE kiriku juures — kirik on ka meditsiinipunkt | punane |
| E02 | Sihtmärkidel puudub tuvastuskriteerium ja -aeg | kollane |
| E03 | Lõhkamine maanteel nr 3, silla mõju hindamata | kollane |
| P01 | 400 tsiviili, tulelöögid H+5…H+9, CDE puudub | kollane |
| P02 | Evakuatsioon algab H+2, lõpp ja kinnitus puuduvad | kollane |
| P03 | Eelhoiatusel puudub kanal | kollane |
| P05 | Katkestamise kriteerium puudub | kollane |
| V01 | T1 eesmärk ja alternatiiv põhjendamata | kollane |
| V02 | SM4 on seotud konkreetse manöövriga | roheline |
| V06 | Tsiviilide evakuatsioon on korraldatud | roheline |

## Testid

```bash
cd ~/legad-github
python3 -m pytest tests -q
```

## Õigusallikad ja nende staatus

| Allikas | Kas tööriist kasutab | Märkus |
|---|---|---|
| IHL: AP I, GC I–IV, CCW, kultuurivara, meditsiin | **jah** | Grete register IHL-R01…R47 |
| Eesti õigus: KKS § 44–49, KORKS § 40, PS § 123 | **jah** | režiim, pädevus, vananenud viited |
| **Sanremo ROE Handbook** (IIHL, 2009) | **jah — ainus ROE-allikas** | ROE on piirang, mis ei tohi ületada seadust; ROE lisa struktuur (lk 26, 64) |
| ROE-kaart / jõu kasutamise kord | **ainult viide** | sisu on piiratud, tööriist ei tsiteeri ega oleta |

\* L04 tekib ainult siis, kui käsus viitab ROE-le ja see sisaldab piirangut
(nt „ainult enesekaitse“). Viite puudumine on L03 (punane).

Allikate PDF-e selles repos ei ole (autoriõigus, suur maht). Viited ja
kasutusotstarve on failis `allikad.py`; tööriist ise neid käivitamisel ei ava.

Tööriist teeb vahet **seadusel** ja **poliitikal**: ROE piirang (nt „ainult
enesekaitse“) ei ole IHL-i nõue, vaid käskija otsus — see märgistatakse eraldi
(L04). Vastupidine juhtum — ROE lubab rohkem kui IHL — jääb täitmata ja sellest
teatatakse (KKS § 44 lg 4–5).

Lisa .docx-is on
eraldi sektsioon **„Allikad ja katvus“** koos täpsete viidetega ja nimekirjaga,
mida see lisa teadlikult ei kata.

## Piirid

- Ei anna lõplikku õiguslikku hinnangut ega kasuta sõnu „lubatud/keelatud“.
- Ei käsitle veel vange, relvi, keskkonda ega rahvusvahelist koostööd.
- Ei asenda LEGAD-i ega komandöri; lisa on mustand.
- Päris LEGAD lisa malli hetkel ei ole — struktuur on tuletatud kolmest
  põhimõttest ja Grete IHL-registrist (`grete/IHL_NOUDED.md`).
