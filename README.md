# CiviCRM MCP Server (Python)

Ein minimal lauffähiger **Model Context Protocol (MCP)** Server für **CiviCRM APIv4** in Python.
Er stellt generische CRUD- und Query-Tools bereit und kann per **stdio** gestartet werden.

## Features
- Tools: `civicrm.create`, `civicrm.get`, `civicrm.update`, `civicrm.delete`, `civicrm.search`  
- Extras: `civicrm.batch`, `civicrm.schema.entities`, `civicrm.schema.fields`
- Async mit `httpx` und `mcp` (FastMCP)
- Config via `.env` (URL, Token, Auth-Schema etc.)
- Einfacher Schema-Cache (in-memory)

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

## Tools & Payloads

### civicrm.create
```json
{
  "entity": "Contact",
  "record": { "contact_type": "Individual", "first_name": "Alice" }
}
```

### civicrm.get
```json
{ "entity": "Contact", "id": 123, "select": ["id","display_name"], "include": ["email"] }
```

### civicrm.update
```json
{ "entity": "Contact", "id": 123, "record": { "first_name": "Alicia" } }
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

## Hinweise
- Auth-Header werden über `AUTH_SCHEME` gewählt: `bearer` → `Authorization: Bearer <TOKEN>`,  
  `x-civi-auth` → `X-Civi-Auth: <TOKEN>`.
- APIv4 erwartet POST JSON `{ entity, action, params }` auf `CIVI_URL` (z. B. `https://example.org/civicrm/api4`). 
- Rückgabestruktur wird unverändert zurückgegeben (inkl. `is_error`, `values` etc.).
- Fehler werden als MCP-Tool-Fehler mit Details geworfen.

## Lizenz
MIT

## Aufsetzen des MCP-Servers mit Claude-Desktop
Claude Desktop ist eines der Standard-Vorschläge zum Testen von MCP-Servern.
Dieses Setup kann zeigen, welche prinzipiellen Möglichkeiten es in Zusammenarbeit von LLMs mit CiviCRM gibt.
Die Fragen des Datenschutzes sind in diesem Setup bei weitem nicht geklärt: Cluade Desktop fragt zwar immer bei allen Zugriffen auf das CiviCRM, ob er dies durchführen soll, aber dann werden die Daten auf den Claude-Servern verarbeitet und die Fragen nach einer vollständigen Löschung bleiben unbeantwortet.
Und bitte vorsichtig, da diese Implementierung über den vollständigen Funktionsumfang von APIV4 verfügt. Mit ein paar Befehlen ist schnell ein ganzen CiviCRM gelöscht!

Zu den Umsetzungsschritten

1) Claude-Desktop installieren, siehe hier https://support.claude.com/de/articles/10065433-claude-desktop-installieren
2) eine claude_desktop_config.json konfiguriren: den Pfad zu dem Installationsverzeichnis, den CiviCRM-Pfad,Site-key und API-Key einsetzen.
3) die claude_desktop_config.json an die richtige Stelle kopieren: unter Linux zu /home/???/.config/Claude/
4) Claude-Desktop aufrufen und nach dem MCP-Server fragen ....