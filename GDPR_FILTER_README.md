# DSGVO-Filterung im CiviCRM MCP Server

## Übersicht

Der CiviCRM MCP Server enthält eine integrierte DSGVO-konforme Filterung, die verhindert, dass personenbezogene Daten aus der CiviCRM-Datenbank ins LLM (Large Language Model) übertragen werden.

## Funktionsweise

### Whitelist-Strategie

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

## Support

Bei Fragen oder Problemen:
1. Prüfen Sie die Logs in `civicrm_mcp.log`
2. Verwenden Sie `GDPRFieldFilter.get_allowed_fields_for_entity(entity)` zur Analyse
3. Kontaktieren Sie den Entwickler für weitere Anpassungen
