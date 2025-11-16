# --- English Version ---------------------------------------------------------------------------
# CiviCRM MCP Server (Python)

A minimally viable **Model Context Protocol (MCP)** server for **CiviCRM APIv4** in Python.
It provides generic CRUD and query tools and can be started via **stdio**.

## Features
- Tools: `civicrm.create`, `civicrm.get`, `civicrm.update`, `civicrm.delete`, `civicrm.search`  
- Extras: `civicrm.batch`, `civicrm.schema.entities`, `civicrm.schema.fields`
- Async with `httpx` and `mcp` (FastMCP)
- Config via `.env` (URL, token, auth schema, etc.)
- Simple schema cache (in-memory)

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Adjust CIVI_URL / CIVI_TOKEN / AUTH_SCHEME
# Example: CIVI_URL=https://example.org/civicrm/api4
#          AUTH_SCHEME=bearer (or x-civi-auth)
#          CIVI_TOKEN=YOUR_TOKEN

python app.py
```

The server communicates MCP over **stdio**. Integrate it into your client/LLM as an MCP server process with stdio transport.

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

## Notes
- Auth headers are selected via `AUTH_SCHEME`: `bearer` → `Authorization: Bearer <TOKEN>`,  
  `x-civi-auth` → `X-Civi-Auth: <TOKEN>`.
- APIv4 expects POST JSON `{ entity, action, params }` to `CIVI_URL` (e.g., `https://example.org/civicrm/api4`). 
- Return structure is returned unchanged (including `is_error`, `values`, etc.).
- Errors are thrown as MCP tool errors with details.

## License
MIT

## Setting Up the MCP Server with Claude Desktop
Claude Desktop is one of the standard recommendations for testing MCP servers.
This setup can demonstrate the fundamental possibilities of LLM collaboration with CiviCRM.
Privacy issues are far from resolved in this setup: Claude Desktop does ask for permission before all CiviCRM accesses, but then the data is processed on Claude's servers and questions about complete deletion remain unanswered.
And please be careful, as this implementation has access to the full functionality of APIv4. With just a few commands, an entire CiviCRM can quickly be deleted!

Implementation steps:

1) Install Claude Desktop, see here https://support.claude.com/de/articles/10065433-claude-desktop-installieren
2) Configure a claude_desktop_config.json: insert the path to the installation directory, the CiviCRM path, site key, and API key.
3) Copy the claude_desktop_config.json to the correct location: on Linux to /home/???/.config/Claude/
4) Launch Claude Desktop and ask about the MCP server....

# --- German Version ---------------------------------------------------------------------------
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