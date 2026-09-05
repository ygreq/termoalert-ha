# TermoAlert București (CMTEB) — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/ygreq/termoalert-ha?style=flat-square)](https://github.com/ygreq/termoalert-ha/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Integrare Home Assistant pentru monitorizarea în timp real a avariilor și întreruperilor de furnizare a apei calde și încălzirii din municipiul București, folosind datele oficiale publicate de **Compania Municipală Termoenergetica București (CMTEB)**.

---

## 📑 Cuprins

* [🌟 Caracteristici principale](#caracteristici-principale)
* [📦 Instalare](#instalare)
  * [Metoda 1: Prin HACS (Recomandat)](#instalare-hacs)
  * [Metoda 2: Instalare manuală](#instalare-manuala)
* [⚙️ Configurare](#configurare)
  * [💡 Cum funcționează căutarea (Stradă vs. Bloc vs. Punct termic)](#cum-functioneaza-cautarea)
  * [📖 Glosar Termeni & Abrevieri CMTEB](#glosar-termeni-abrevieri-cmteb)
    * [📊 Tabel comparativ stări senzor](#tabel-comparativ-stari)
* [💡 Exemple de Automatizări](#exemple-de-automatizari)
  * [1. Pornire automată boiler la avarie](#automatizare-pornire-boiler)
  * [2. Oprire boiler la remediere](#automatizare-oprire-boiler)
* [📊 Exemple Carduri Lovelace](#exemple-carduri-lovelace)
  * [1. Card Standard (Entities cu numărătoare inversă condiționată)](#card-standard-entities)
  * [2. Card Mushroom (Opțional)](#card-mushroom)
* [⚖️ Sursă de Date & Disclaimer](#sursa-de-date-disclaimer)

---

<a id="caracteristici-principale"></a>
## 🌟 Caracteristici principale

* **Configurare 100% din interfața vizuală (UI):** Fără linii de cod în `configuration.yaml`.
* **Suport multi-adresă:** Poți adăuga mai multe adrese/zone (ex: *Acasă*, *Părinți*, *Birou*).
* **Căutare inteligentă cu normalizare automată:**
  * Ignoră automat diacriticele (`ș/ş` ➔ `s`, `ț/ţ` ➔ `t`, `ă/â` ➔ `a`, `î` ➔ `i`).
  * Recunoaște abrevierile uzuale (`strada` = `str`, `bulevardul` = `bld`, `soseaua` = `sos`, `aleea` = `ale`, etc.).
  * Permite căutare după numele străzii, numărul de bloc sau direct după numele punctului termic.
* **Entități create pentru fiecare adresă configurată:**
  * 🔴 **`binary_sensor.<adresa>_outage`**: Clasă `problem` (`Problemă` / `on` = avarie/deficiență activă, `OK` / `off` = normal).
    * *Atribute bogate:* cauza avariei, tipul agentului afectat, data/ora estimată de remediere, punctul termic și adresa exactă identificată.
  * ℹ️ **`sensor.<adresa>_service_status`**: Mesaj clar și concis în limba română (ex: `Normal`, `Deficiență apă caldă`, `Oprire apă caldă`, `Deficiență încălzire`).
  * ⏳ **`sensor.<adresa>_time_remaining`**: Numărătoare inversă formatată în zile și ore până la remediere (ex: `13 zile și 11 ore`).
  * ⏱️ **`sensor.<adresa>_estimated_restoration`**: Data și ora preconizate pentru repunerea în funcțiune.
  * 🏙️ **`sensor.<adresa>_sector_outages`**: Numărul total de avarii active din întregul sector.
* **Interval de actualizare configurabil:** Implicit 15 minute (reglabil între 5 și 120 de minute din meniul *Configure*).
* **Bilingv:** Suport complet pentru Română și Engleză.

---

<a id="instalare"></a>
## 📦 Instalare

<a id="instalare-hacs"></a>
### Metoda 1: Prin HACS (Recomandat)

1. Deschide **HACS** în Home Assistant.
2. Dă clic pe cele 3 puncte din colțul dreapta-sus și selectează **Custom repositories**.
3. La **Repository** adaugă URL-ul repository-ului tău:
   ```text
   https://github.com/ygreq/termoalert-ha
   ```
4. La **Type / Category** selectează **Integration**.
5. Dă clic pe **Add**.
6. Caută acum în HACS **TermoAlert București (CMTEB)** și apasă **Download**.
7. **Repornește Home Assistant** (`Settings` -> `System` -> `Restart`).

<a id="instalare-manuala"></a>
### Metoda 2: Instalare manuală

1. Descarcă arhiva release-ului sau clonează repository-ul.
2. Copiază folderul `custom_components/termoalert` în directorul `/config/custom_components/` din instanța ta de Home Assistant.
3. Repornește Home Assistant.

---

<a id="configurare"></a>
## ⚙️ Configurare

1. În Home Assistant, mergi la **Settings (Setări)** ➔ **Devices & Services (Dispozitive și servicii)**.
2. Apasă pe butonul **Add Integration (+ Adaugă integrare)**.
3. Caută **TermoAlert București (CMTEB)**.
4. Completează datele:
   * **Sectorul:** Selectează sectorul (1 - 6).
5. Apasă **Submit**. Dispozitivul și senzorii vor fi creați automat!

---

<a id="cum-functioneaza-cautarea"></a>
### 💡 Cum funcționează căutarea (Stradă vs. Indicativ Bloc vs. Punct termic)

> [!IMPORTANT]
> **Formatul adreselor în evidențele CMTEB:**  
> În baza de date oficială a Termoenergetica (CMTEB), adresele sunt înregistrate după **stradă și indicativul blocului** (ex: `bl. A1`, `bl. M12`, `bl. 403`), **NU după numărul poștal al străzii** (nu se folosesc numere de tipul „nr. 25” sau „nr. 104” pentru imobile colective).

#### Cum să alegi termenul de căutare:

| Ce introduci la căutare | Exemple generice | Ce rezultate primești |
|---|---|---|
| **Indicativul blocului tău** *(Recomandat pentru precizie maximă)* | `A12` sau `bl. 403` | Alerte **strict** când blocul tău este afectat de o avarie sau deficiență. |
| **Numele străzii** | `Iancului` sau `Măgura Vulturului` | Alerte pentru **orice avarie** de pe acea stradă (chiar dacă afectează alt punct termic sau alt tronson de pe stradă). |
| **Numele punctului termic** | `21 Pantelimon` | Alerte pentru toate blocurile alimentate de acel punct termic. |

*Căutarea include normalizare automată:* poți scrie fără diacritice, cu litere mari sau mici, iar abrevierile comune (`strada` = `str`, `bulevardul` = `bld`, `soseaua` = `sos`, `aleea` = `ale`) sunt recunoscute automat.

> [!TIP]
> **Cum afli denumirea exactă a blocului sau a punctului tău termic:**  
> Poți verifica în timp real cum sunt denumite oficial punctele termice și blocurile arondate pe pagina CMTEB:  
> 🔗 **[Funcționare sistem termoficare CMTEB](https://cmteb.ro/functionare_sistem_termoficare.php)**  
> Selectează tab-ul sectorului tău și folosește `Ctrl + F` pentru a căuta strada ta. Vei vedea lista exactă cu punctul termic și indicativele blocurilor afectate.

---

<a id="glosar-termeni-abrevieri-cmteb"></a>
### 📖 Glosar Termeni & Abrevieri CMTEB

În rapoartele și comunicatele oficiale CMTEB (Termoenergetica) vei întâlni frecvent aceste prescurtări:

* **`ACC`**: **A**pă **C**aldă de **C**onsum (furnizată la robinet / duș).
* **`ÎNC`**: **Înc**ălzire (agentul termic pentru calorifere).
* **`Oprire ACC`**: Furnizarea apei calde este **oprită complet**.
* **`Deficiență ACC`**: Apa caldă nu este sistată complet, dar este livrată **sub parametrii contractuali** (debit scăzut sau vine doar călâie/rece din cauza lipsei de presiune sau de temperatură din rețeaua primară).
* **`Oprire ÎNC`**: Furnizarea căldurii în calorifere este oprită complet.
* **`Deficiență ÎNC`**: Agentul termic pentru calorifere este livrat sub parametri contractuali (calorifere doar călâi).

> [!NOTE]
> Integrarea TermoAlert interpretează automat aceste coduri tehnice și afișează direct mesaje explicite în limba română în starea senzorului (`sensor.<adresa>_service_status`).

<a id="tabel-comparativ-stari"></a>
#### 📊 Tabel comparativ pentru toate stările:

| Stare senzor | Descriere | Notare tehnică CMTEB |
|---|---|---|
| **`Normal`** | Serviciul funcționează în parametri normali (fără avarie) | — |
| **`Deficiență apă caldă`** | Apă caldă livrată sub parametri contractuali (apă călâie / debit și presiune reduse) | `Deficienta ACC` |
| **`Oprire apă caldă`** | Furnizarea apei calde este sistată complet | `Oprire ACC` |
| **`Deficiență încălzire`** | Agentul termic pentru calorifere nu atinge temperatura optimă (calorifere călâi) | `Deficienta INC` |
| **`Oprire încălzire`** | Furnizarea încălzirii în calorifere este oprită complet | `Oprire INC` |
| **`Deficiență apă & căldură`** | Atât apa caldă, cât și încălzirea sunt furnizate sub parametri contractuali | `Deficienta ACC / INC` |
| **`Oprire apă & căldură`** | Atât apa caldă, cât și încălzirea sunt oprite complet | `Oprire ACC / INC` |

---

<a id="exemple-de-automatizari"></a>
## 💡 Exemple de Automatizări

<a id="automatizare-pornire-boiler"></a>
### 1. Pornire automată boiler electric când apare o avarie de apă caldă

```yaml
alias: "TermoAlert - Comutare Boiler la Avarie"
description: "Pornește boilerul dacă apa caldă este oprită de CMTEB"
trigger:
  - platform: state
    entity_id: binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage
    to: "on"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.boiler_electric
  - service: notify.notify
    data:
      title: "⚠️ Avarie Termoenergetica!"
      message: >
        S-a oprit apa caldă la adresa ta. 
        Cauza: {{ state_attr('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'cauza') }}
        Remediere estimată: {{ state_attr('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'estimare_punere_in_functiune') }}
        Boilerul electric a fost pornit automat.
```

<a id="automatizare-oprire-boiler"></a>
### 2. Oprire boiler când avaria a fost remediată de CMTEB

```yaml
alias: "TermoAlert - Oprire Boiler la Remediere"
description: "Oprește boilerul când apa caldă revine la parametri"
trigger:
  - platform: state
    entity_id: binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage
    to: "off"
action:
  - service: switch.turn_off
    target:
      entity_id: switch.boiler_electric
  - service: notify.notify
    data:
      title: "✅ Avarie Termoenergetica Remediată"
      message: "Furnizarea apei calde a revenit la normal. Boilerul a fost oprit."
```

---

<a id="exemple-carduri-lovelace"></a>
## 📊 Exemple Carduri Lovelace

<a id="card-standard-entities"></a>
### 1. Card Standard (Entities Card cu numărătoare inversă condiționată)

Rândurile pentru **Timp Rămas Până la Remediere** și **Data Estimată Remediere** apar automat **doar dacă există o avarie activă** (`Problemă` / `on`):

```yaml
type: entities
title: TermoAlert
entities:
  - entity: binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage
    name: Avarie Activă
  - entity: sensor.termoalert_sector_2_elev_stefan_stefanescu_service_status
    name: Stare Serviciu
  - type: conditional
    conditions:
      - entity: binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage
        state: "on"
    row:
      entity: sensor.termoalert_sector_2_elev_stefan_stefanescu_time_remaining
      name: Timp Rămas Până la Remediere
  - type: conditional
    conditions:
      - entity: binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage
        state: "on"
    row:
      entity: sensor.termoalert_sector_2_elev_stefan_stefanescu_estimated_restoration
      name: Data Estimată Remediere
  - entity: sensor.termoalert_sector_2_elev_stefan_stefanescu_sector_outages
    name: Total Avarii Sector
```

<a id="card-mushroom"></a>
### 2. Card Mushroom (Opțional)

Dacă folosești **Mushroom Cards** din HACS:

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-template-card
    primary: Termoenergetica (Acasă)
    secondary: >
      {% if is_state('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'on') %}
        {{ state_attr('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'agent_afectat') }} - Până la: {{ state_attr('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'estimare_punere_in_functiune') }}
      {% else %}
        Serviciu activ în parametri normali
      {% endif %}
    icon: >
      {% if is_state('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'on') %}
        mdi:water-boiler-off
      {% else %}
        mdi:water-boiler
      {% endif %}
    icon_color: >
      {% if is_state('binary_sensor.termoalert_sector_2_elev_stefan_stefanescu_outage', 'on') %}
        red
      {% else %}
        green
      {% endif %}
```

---

<a id="sursa-de-date-disclaimer"></a>
## ⚖️ Sursă de Date & Disclaimer

* Datele sunt preluate public din secțiunea oficială [Funcționare sistem termoficare](https://cmteb.ro/functionare_sistem_termoficare.php) a Companiei Municipale Termoenergetica București S.A.
* Acest proiect este o inițiativă independentă open-source și nu este sponsorizat, afiliat sau dezvoltat direct de CMTEB.
* Licență: **MIT**.
