# CiviCRM MCP Server with GDPR Filtering

A **Model Context Protocol (MCP)** server for **CiviCRM APIv4** in Python with integrated GDPR-compliant data filtering.

[🇩🇪 Deutsche Version](#deutsche-version) | [🇬🇧 English Version](#english-version)

---

## English Version

### Overview

This MCP server provides generic CRUD and query tools for CiviCRM APIv4 and can be started via **stdio**. It includes built-in GDPR-compliant filtering that prevents personally identifiable information (PII) from being transferred to the LLM (Large Language Model).

### Key Features

- **CRUD Tools**: `civicrm.create`, `civicrm.get`, `civicrm.update`, `civicrm.delete`, `civicrm.search`
- **Additional Tools**: `civicrm.batch`, `civicrm.schema.entities`, `civicrm.schema.fields`
- **GDPR Filtering**: Automatic filtering of PII before data reaches the LLM
- **Async Architecture**: Built with `httpx` and `mcp` (FastMCP)
- **Configuration**: Via `.env` file (URL, token, auth schema, etc.)
- **Schema Cache**: Simple in-memory caching

### Quickstart

> A note on Python: the following commands may need to be run with `python3` instead of `python`, and `pip3` instead of `pip`. 

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Configure CIVI_URL / CIVI_TOKEN / AUTH_SCHEME
# Example: CIVI_URL=https://example.org/civicrm/api4
#          AUTH_SCHEME=bearer (or x-civi-auth)
#          CIVI_TOKEN=YOUR_TOKEN

python app.py
```

The server communicates via **stdio** using the MCP protocol. Integrate it into your client/LLM as an MCP server process with stdio transport.

### Available Tools

#### civicrm.create
```json
{
  "entity": "Contact",
  "record": { "contact_type": "Individual", "first_name": "Alice" }
}
```

#### civicrm.get
```json
{ 
  "entity": "Contact", 
  "id": 123, 
  "select": ["id","display_name"], 
  "include": ["email"] 
}
```

#### civicrm.update
```json
{ 
  "entity": "Contact", 
  "id": 123, 
  "record": { "first_name": "Alicia" } 
}
```

#### civicrm.delete
```json
{ "entity": "Contact", "id": 123 }
```

#### civicrm.search
```json
{
  "entity": "Contact",
  "where": [{"field":"contact_type","op":"=","value":"Individual"}],
  "select": ["id","display_name"],
  "include": ["email"],
  "orderBy": {"id": "DESC"},
  "limit": 25,
  "offset": 0
}
```

#### civicrm.batch
```json
{
  "operations": [
    {"entity":"Contact","action":"get","params":{"where":[{"field":"id","op":"=","value":1}]}},
    {"entity":"Contact","action":"create","params":{"first_name":"Bob","contact_type":"Individual"}}
  ]
}
```

#### civicrm.schema.entities
```json
{}
```

#### civicrm.schema.fields
```json
{ "entity": "Contact", "forceRefresh": false }
```

---

## GDPR Filtering

### How It Works

#### Whitelist Strategy

The `GDPRFieldFilter` uses a **whitelist approach**: Only explicitly safe-listed fields are allowed through. All other fields are automatically filtered out.

#### Filtered Data

##### 🔴 CRITICAL - Always Filtered:

**Contact Entity:**
- Names: `first_name`, `middle_name`, `last_name`, `display_name`, `sort_name`, `nick_name`, `legal_name`
- Organization names: `organization_name`, `household_name`
- Birth dates: `birth_date`, `deceased_date`
- Images: `image_URL`
- Personalized greetings: `email_greeting_display`, `postal_greeting_display`, `addressee_display`
- Security tokens: `hash`, `api_key`
- Identifiers: `legal_identifier` (SSN, TIN, etc.)

**Address Entity:**
- Full address: `street_address`, `street_number`, `street_name`, `street_unit`
- Additional address lines: `supplemental_address_1`, `supplemental_address_2`, `supplemental_address_3`
- City: `city`
- Postal code: `postal_code`, `postal_code_suffix`
- GPS coordinates: `geo_code_1`, `geo_code_2`

**Email Entity:**
- Email address: `email`

**Phone Entity:**
- Phone numbers: `phone`, `phone_ext`, `phone_numeric`

**Activity/Note:**
- Content: `subject`, `details`, `note`, `location`

##### 🟢 SAFE - Allowed Through:

**Metadata & IDs:**
- All ID fields: `id`, `contact_id`, `*_id`
- Timestamps: `created_date`, `modified_date`
- Types and status: `contact_type`, `status_id`, `is_deleted`, etc.

**Preferences (no PII):**
- `do_not_email`, `do_not_phone`, `do_not_mail`, `do_not_sms`, `do_not_trade`
- `is_opt_out`, `preferred_communication_method`, `preferred_language`

**Aggregated Data:**
- `age_years` (age in years, not birth date!)
- `county_id`, `state_province_id`, `country_id` (IDs only, not names)

### Anonymized Replacement Fields

The filter automatically adds anonymized placeholders:

**Contact:**
```json
{
  "id": 123,
  "_display_name": "Contact #123",
  "_has_birth_date": true,
  "_filtered_fields": ["first_name", "last_name", "birth_date"]
}
```

**Address:**
```json
{
  "id": 456,
  "contact_id": 123,
  "country_id": 1,
  "_has_address": true,
  "_location_level": "country",
  "_filtered_fields": ["street_address", "postal_code", "city"]
}
```

**Email:**
```json
{
  "id": 789,
  "contact_id": 123,
  "is_primary": 1,
  "_has_email": true,
  "_filtered_fields": ["email"]
}
```

### Applied Tools

Filtering is automatically applied to the following tools:

- ✅ `civicrm_get` - Retrieve single record
- ✅ `civicrm_search` - Search/list of records
- ✅ `civicrm_update_request` - Shows current values before update
- ✅ `civicrm_delete_request` - Shows record before deletion
- ✅ `civicrm_batch` - For GET operations in batches

### Non-Filtered Tools:

- `civicrm_create` - Only writes data, doesn't read
- `civicrm_update_confirmed` - Only writes data
- `civicrm_delete_confirmed` - Only deletes data
- `civicrm_schema_entities` - Only shows entity names
- `civicrm_schema_fields` - Only shows field metadata, no values

### Implementation

#### File Structure

```
├── app.py                  # MCP Server (modified)
├── civicrm_client.py       # CiviCRM API Client (unchanged)
├── gdpr_filter.py          # New GDPR filter class
└── schema_cache.py         # Schema Cache (unchanged)
```

#### Main Class: `GDPRFieldFilter`

```python
from gdpr_filter import GDPRFieldFilter

# Filter response
filtered = GDPRFieldFilter.filter_response(entity="Contact", response=api_response)

# Check single field
is_allowed = GDPRFieldFilter.is_field_allowed(entity="Contact", field="first_name")
# → False

is_allowed = GDPRFieldFilter.is_field_allowed(entity="Contact", field="id")
# → True
```

### Extension

#### Adding a New Entity

To configure a new entity, edit `gdpr_filter.py`:

```python
ALLOWED_FIELDS = {
    'MyEntity': {
        'id',
        'status_id',
        'created_date',
        # ... other safe fields
    }
}

AGGREGATE_FIELDS = {
    'MyEntity': {
        'sensitive_field_1',
        'sensitive_field_2',
        # ... PII fields
    }
}
```

#### Logging

The filter automatically logs all filtered fields:

```
[DEBUG] civicrm-mcp.gdpr: Removed 8 fields from Contact: ['first_name', 'last_name', ...]
[DEBUG] civicrm-mcp.gdpr: Filtered Contact response: 10 records
```

### Security Notes

1. **Unknown Entities**: For entities not defined in `ALLOWED_FIELDS`, only ID fields are allowed through (very restrictive).

2. **Custom Fields**: Custom fields are NOT allowed by default and must be explicitly added to the whitelist.

3. **IDs are always allowed**: All fields ending in `_id` or `.id` are allowed through. IDs themselves are not PII, but references.

4. **No bypass**: Filtering occurs **after** the CiviCRM API call and **before** returning to the LLM. There is no way to bypass the filtering.

### Testing

```python
# Create test file
import asyncio
from app import civicrm_get, GetInput

async def test_gdpr_filter():
    # Retrieve contact with PII
    result = await civicrm_get(GetInput(entity="Contact", id=123))
    
    # Check: first_name should NOT be in response
    assert "first_name" not in result
    
    # Check: _display_name should be present
    assert "_display_name" in result
    
    # Check: id should be present
    assert "id" in result

asyncio.run(test_gdpr_filter())
```

### Compliance

This implementation complies with GDPR requirements:

- ✅ **Data Minimization** (Art. 5(1)(c) GDPR): Only necessary data is processed
- ✅ **Purpose Limitation** (Art. 5(1)(b) GDPR): Data is only used for defined purposes
- ✅ **Data Minimization**: PII is filtered out
- ✅ **Transparency**: Filtered fields are listed in `_filtered_fields`

---

## Setting Up with Claude Desktop

Claude Desktop is one of the standard recommendations for testing MCP servers. This setup demonstrates the fundamental possibilities of LLM collaboration with CiviCRM.

**⚠️ Privacy Warning**: Privacy issues are far from resolved in this setup. Claude Desktop does ask for permission before all CiviCRM accesses, but data is then processed on Claude's servers and questions about complete deletion remain unanswered. Be careful, as this implementation has access to the full functionality of APIv4. With just a few commands, an entire CiviCRM can quickly be deleted!

### Implementation Steps:

1. **Install Claude Desktop**: See [installation guide](https://support.claude.com/en/articles/10065433-install-claude-desktop)
2. **Configure `claude_desktop_config.json`**: Insert the path to the installation directory, CiviCRM path, site key, and API key
3. **Copy the config file**: On Linux to `/home/???/.config/Claude/`
4. **Launch Claude Desktop** and ask about the MCP server

---

## Technical Notes

- Auth headers are selected via `AUTH_SCHEME`: `bearer` → `Authorization: Bearer <TOKEN>`, `x-civi-auth` → `X-Civi-Auth: <TOKEN>`
- APIv4 expects POST JSON `{ entity, action, params }` to `CIVI_URL` (e.g., `https://example.org/civicrm/api4`)
- Return structure is returned unchanged (including `is_error`, `values`, etc.)
- Errors are thrown as MCP tool errors with details

---

## Support

For questions or issues:
1. Check the logs in `civicrm_mcp.log`
2. Use `GDPRFieldFilter.get_allowed_fields_for_entity(entity)` for analysis
3. Contact the developer for further customizations

---

## License

MIT

---
---

# Deutsche Version

## Übersicht
1) Install Claude Desktop, see here https://support.claude.com/en/articles/10065433-installing-claude-desktop
2) Configure a claude_desktop_config.json: insert the path to the installation directory, the CiviCRM path, site key, and API key (see `example_claude_desktop_config.json`)
3) Copy the claude_desktop_config.json to the correct location: on Linux to `/home/???/.config/Claude/`, on Mac to `~/Library/Application Support/Claude/`
4) Launch Claude Desktop and ask about the MCP server....

Dieser MCP-Server stellt generische CRUD- und Query-Tools für CiviCRM APIv4 bereit und kann per **stdio** gestartet werden. Er enthält eine integrierte DSGVO-konforme Filterung, die verhindert, dass personenbezogene Daten aus der CiviCRM-Datenbank ins LLM (Large Language Model) übertragen werden.

## Hauptfunktionen

- **CRUD-Tools**: `civicrm.create`, `civicrm.get`, `civicrm.update`, `civicrm.delete`, `civicrm.search`
- **Zusatz-Tools**: `civicrm.batch`, `civicrm.schema.entities`, `civicrm.schema.fields`
- **DSGVO-Filterung**: Automatische Filterung personenbezogener Daten vor Übertragung ans LLM
- **Async-Architektur**: Mit `httpx` und `mcp` (FastMCP)
- **Konfiguration**: Via `.env`-Datei (URL, Token, Auth-Schema etc.)
- **Schema-Cache**: Einfaches In-Memory-Caching

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Passe CIVI_URL / CIVI_TOKEN / AUTH_SCHEME an
# Beispiel: CIVI_URL=https://example.org/civicrm/api4
#           AUTH_SCHEME=bearer (oder x-civi-auth)
#           CIVI_TOKEN=DEIN_TOKEN

python app.py
```

Der Server spricht MCP über **stdio**. Binde ihn in deinen Client/LLM ein als MCP-Server-Prozess mit stdio-Transport.

## Verfügbare Tools

### civicrm.create
```json
{
  "entity": "Contact",
  "record": { "contact_type": "Individual", "first_name": "Alice" }
}
```

### civicrm.get
```json
{ 
  "entity": "Contact", 
  "id": 123, 
  "select": ["id","display_name"], 
  "include": ["email"] 
}
```

### civicrm.update
```json
{ 
  "entity": "Contact", 
  "id": 123, 
  "record": { "first_name": "Alicia" } 
}
```

### civicrm.delete
```json
{ "entity": "Contact", "id": 123 }
```

### civicrm.search
```json
{
  "entity": "Contact",
  "where": [{"field":"contact_type","op":"=","value":"Individual"}],
  "select": ["id","display_name"],
  "include": ["email"],
  "orderBy": {"id": "DESC"},
  "limit": 25,
  "offset": 0
}
```

### civicrm.batch
```json
{
  "operations": [
    {"entity":"Contact","action":"get","params":{"where":[{"field":"id","op":"=","value":1}]}},
    {"entity":"Contact","action":"create","params":{"first_name":"Bob","contact_type":"Individual"}}
  ]
}
```

### civicrm.schema.entities
```json
{}
```

### civicrm.schema.fields
```json
{ "entity": "Contact", "forceRefresh": false }
```

---

## DSGVO-Filterung

### Funktionsweise

#### Whitelist-Strategie

Der `GDPRFieldFilter` verwendet einen **Whitelist-Ansatz**: Nur explizit als sicher eingestufte Felder werden durchgelassen. Alle anderen Felder werden automatisch herausgefiltert.

### Gefilterte Daten

#### 🔴 KRITISCH - Immer gefiltert:

**Contact Entity:**
- Namen: `first_name`, `middle_name`, `last_name`, `display_name`, `sort_name`, `nick_name`, `legal_name`
- Organisationsnamen: `organization_name`, `household_name`
- Geburtsdaten: `birth_date`, `deceased_date`
- Bilder: `image_URL`
- Personalisierte Grußformeln: `email_greeting_display`, `postal_greeting_display`, `addressee_display`
- Sicherheits-Tokens: `hash`, `api_key`
- Identifikatoren: `legal_identifier` (SSN, TIN, etc.)

**Address Entity:**
- Vollständige Adresse: `street_address`, `street_number`, `street_name`, `street_unit`
- Adresszusätze: `supplemental_address_1`, `supplemental_address_2`, `supplemental_address_3`
- Ort: `city`
- PLZ: `postal_code`, `postal_code_suffix`
- GPS-Koordinaten: `geo_code_1`, `geo_code_2`

**Email Entity:**
- E-Mail-Adresse: `email`

**Phone Entity:**
- Telefonnummern: `phone`, `phone_ext`, `phone_numeric`

**Activity/Note:**
- Inhalte: `subject`, `details`, `note`, `location`

#### 🟢 SICHER - Durchgelassen:

**Metadaten & IDs:**
- Alle ID-Felder: `id`, `contact_id`, `*_id`
- Timestamps: `created_date`, `modified_date`
- Typen und Status: `contact_type`, `status_id`, `is_deleted`, etc.

**Präferenzen (keine personenbezogenen Daten):**
- `do_not_email`, `do_not_phone`, `do_not_mail`, `do_not_sms`, `do_not_trade`
- `is_opt_out`, `preferred_communication_method`, `preferred_language`

**Aggregierte Daten:**
- `age_years` (Alter in Jahren, nicht Geburtsdatum!)
- `county_id`, `state_province_id`, `country_id` (nur IDs, nicht Namen)

### Anonymisierte Ersatzfelder

Der Filter fügt automatisch anonymisierte Platzhalter hinzu:

**Contact:**
```json
{
  "id": 123,
  "_display_name": "Contact #123",
  "_has_birth_date": true,
  "_filtered_fields": ["first_name", "last_name", "birth_date"]
}
```

**Address:**
```json
{
  "id": 456,
  "contact_id": 123,
  "country_id": 1,
  "_has_address": true,
  "_location_level": "country",
  "_filtered_fields": ["street_address", "postal_code", "city"]
}
```

**Email:**
```json
{
  "id": 789,
  "contact_id": 123,
  "is_primary": 1,
  "_has_email": true,
  "_filtered_fields": ["email"]
}
```

## Angewendete Tools

Die Filterung wird automatisch bei folgenden Tools angewendet:

- ✅ `civicrm_get` - Einzelner Record abrufen
- ✅ `civicrm_search` - Suche/Liste von Records
- ✅ `civicrm_update_request` - Zeigt aktuelle Werte vor Update
- ✅ `civicrm_delete_request` - Zeigt Record vor Löschung
- ✅ `civicrm_batch` - Bei GET-Operationen in Batches

### Nicht gefilterte Tools:

- `civicrm_create` - Schreibt nur Daten, liest keine
- `civicrm_update_confirmed` - Schreibt nur Daten
- `civicrm_delete_confirmed` - Löscht nur Daten
- `civicrm_schema_entities` - Zeigt nur Entity-Namen
- `civicrm_schema_fields` - Zeigt nur Feld-Metadaten, keine Werte

## Implementierung

### Dateistruktur

```
├── app.py                  # MCP Server (modifiziert)
├── civicrm_client.py       # CiviCRM API Client (unverändert)
├── gdpr_filter.py          # Neue DSGVO-Filterklasse
└── schema_cache.py         # Schema Cache (unverändert)
```

### Hauptklasse: `GDPRFieldFilter`

```python
from gdpr_filter import GDPRFieldFilter

# Response filtern
filtered = GDPRFieldFilter.filter_response(entity="Contact", response=api_response)

# Einzelnes Feld prüfen
is_allowed = GDPRFieldFilter.is_field_allowed(entity="Contact", field="first_name")
# → False

is_allowed = GDPRFieldFilter.is_field_allowed(entity="Contact", field="id")
# → True
```

## Erweiterung

### Neue Entity hinzufügen

Um eine neue Entity zu konfigurieren, bearbeiten Sie `gdpr_filter.py`:

```python
ALLOWED_FIELDS = {
    'MyEntity': {
        'id',
        'status_id',
        'created_date',
        # ... weitere sichere Felder
    }
}

AGGREGATE_FIELDS = {
    'MyEntity': {
        'sensitive_field_1',
        'sensitive_field_2',
        # ... personenbezogene Felder
    }
}
```

### Logging

Der Filter loggt automatisch alle gefilterten Felder:

```
[DEBUG] civicrm-mcp.gdpr: Removed 8 fields from Contact: ['first_name', 'last_name', ...]
[DEBUG] civicrm-mcp.gdpr: Filtered Contact response: 10 records
```

## Sicherheitshinweise

1. **Unbekannte Entities**: Bei Entities, die nicht in `ALLOWED_FIELDS` definiert sind, werden nur ID-Felder durchgelassen (sehr restriktiv).

2. **Custom Fields**: Custom Fields sind standardmäßig NICHT erlaubt und müssen explizit zur Whitelist hinzugefügt werden.

3. **IDs sind immer erlaubt**: Alle Felder die auf `_id` oder `.id` enden, werden durchgelassen. IDs selbst sind keine personenbezogenen Daten, aber Verweise.

4. **Keine Umgehung**: Die Filterung erfolgt **nach** dem CiviCRM API-Aufruf und **vor** der Rückgabe ans LLM. Es gibt keine Möglichkeit, die Filterung zu umgehen.

## Testen

```python
# Test-Datei erstellen
import asyncio
from app import civicrm_get, GetInput

async def test_gdpr_filter():
    # Contact mit personenbezogenen Daten abrufen
    result = await civicrm_get(GetInput(entity="Contact", id=123))
    
    # Prüfen: first_name sollte NICHT in der Response sein
    assert "first_name" not in result
    
    # Prüfen: _display_name sollte vorhanden sein
    assert "_display_name" in result
    
    # Prüfen: id sollte vorhanden sein
    assert "id" in result

asyncio.run(test_gdpr_filter())
```

## Compliance

Diese Implementierung entspricht den DSGVO-Anforderungen:

- ✅ **Datensparsamkeit** (Art. 5 Abs. 1 lit. c DSGVO): Nur notwendige Daten werden verarbeitet
- ✅ **Zweckbindung** (Art. 5 Abs. 1 lit. b DSGVO): Daten werden nur für definierte Zwecke verwendet
- ✅ **Datenminimierung**: Personenbezogene Daten werden herausgefiltert
- ✅ **Transparenz**: Gefilterte Felder werden in `_filtered_fields` aufgelistet

---

## Aufsetzen mit Claude Desktop

Claude Desktop ist eines der Standard-Vorschläge zum Testen von MCP-Servern. Dieses Setup kann zeigen, welche prinzipiellen Möglichkeiten es in Zusammenarbeit von LLMs mit CiviCRM gibt.

**⚠️ Datenschutz-Warnung**: Die Fragen des Datenschutzes sind in diesem Setup bei weitem nicht geklärt. Claude Desktop fragt zwar immer bei allen Zugriffen auf das CiviCRM, ob er dies durchführen soll, aber dann werden die Daten auf den Claude-Servern verarbeitet und die Fragen nach einer vollständigen Löschung bleiben unbeantwortet. Bitte vorsichtig, da diese Implementierung über den vollständigen Funktionsumfang von APIv4 verfügt. Mit ein paar Befehlen ist schnell ein ganzes CiviCRM gelöscht!

### Umsetzungsschritte:

1. **Claude Desktop installieren**: Siehe [Installationsanleitung](https://support.claude.com/de/articles/10065433-claude-desktop-installieren)
2. **`claude_desktop_config.json` konfigurieren**: Den Pfad zu dem Installationsverzeichnis, den CiviCRM-Pfad, Site-key und API-Key einsetzen
3. **Config-Datei kopieren**: Unter Linux zu `/home/???/.config/Claude/`
4. **Claude Desktop aufrufen** und nach dem MCP-Server fragen

---

## Technische Hinweise

- Auth-Header werden über `AUTH_SCHEME` gewählt: `bearer` → `Authorization: Bearer <TOKEN>`, `x-civi-auth` → `X-Civi-Auth: <TOKEN>`
- APIv4 erwartet POST JSON `{ entity, action, params }` auf `CIVI_URL` (z. B. `https://example.org/civicrm/api4`)
- Rückgabestruktur wird unverändert zurückgegeben (inkl. `is_error`, `values` etc.)
- Fehler werden als MCP-Tool-Fehler mit Details geworfen

---

## Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Logs in `civicrm_mcp.log`
2. Verwenden Sie `GDPRFieldFilter.get_allowed_fields_for_entity(entity)` zur Analyse
3. Kontaktieren Sie den Entwickler für weitere Anpassungen

---

## Lizenz

MIT
1) Claude-Desktop installieren, siehe hier https://support.claude.com/de/articles/10065433-claude-desktop-installieren
2) eine claude_desktop_config.json konfiguriren: den Pfad zu dem Installationsverzeichnis, den CiviCRM-Pfad,Site-key und API-Key einsetzen.
3) die claude_desktop_config.json an die richtige Stelle kopieren: unter Linux zu `/home/???/.config/Claude/`, unter Mac zu `~/Library/Application Support/Claude/`
4) Claude-Desktop aufrufen und nach dem MCP-Server fragen ....
