import asyncio
import json
import os
from typing import Dict, Any, Literal, Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import CallToolResult, TextContent

from civicrm_client import CiviCRMClient
from schema_cache import SchemaCache
from gdpr_filter import GDPRFieldFilter
import argparse
import sys

app = FastMCP("civicrm-mcp-gdpr")
schema_cache = SchemaCache(ttl_seconds=900)

# ---------- Pydantic Input Models      ----------
class PingInput(BaseModel):
    """Input for ping (no parameters needed)"""
    pass

class CreateInput(BaseModel):
    entity: str = Field(..., description="CiviCRM entity, e.g., Contact")
    record: Dict[str, Any] = Field(..., description="Fields for create()")

class GetInput(BaseModel):
    entity: str
    id: int = Field(..., description="Primary ID")
    select: Optional[List[str]] = None
    include: Optional[List[str]] = None

class UpdateInput(BaseModel):
    entity: str
    id: int
    record: Dict[str, Any]

class DeleteInput(BaseModel):
    entity: str
    id: int

class SearchInput(BaseModel):
    entity: str
    where: Optional[List[List]] = None
    select: Optional[List[str]] = None
    include: Optional[List[str]] = None
    orderBy: Optional[Dict[str, Any]] = None
    limit: Optional[int] = Field(50, ge=1, le=1000)
    offset: Optional[int] = Field(0, ge=0)

class BatchOp(BaseModel):
    entity: str
    action: Literal["get","create","update","delete"]
    params: Dict[str, Any]

class BatchInput(BaseModel):
    operations: List[BatchOp]

class SchemaEntitiesInput(BaseModel):
    """Input for getting schema entities"""
    pass

class SchemaFieldsInput(BaseModel):
    entity: str
    forceRefresh: bool = False

class GetActionsInput(BaseModel):
    entity: str

class SaveInput(BaseModel):
    entity: str
    records: List[Dict[str, Any]] = Field(..., description="Records to save (upsert)")
    defaults: Optional[Dict[str, Any]] = None
    match: Optional[List[str]] = Field(None, description="Fields to match for updates")

class ApiHelpInput(BaseModel):
    """Input for API help (no parameters needed)"""
    pass


# ---------- Helpers ----------
def as_text_output(obj: Any) -> CallToolResult:
    txt = json.dumps(obj, ensure_ascii=False, indent=2)
    return CallToolResult(
        content=[TextContent(type="text", text=txt)],
        structured_content=obj,   # newer MCP spec field (clients can parse JSON)
    )

# ---------- Tools ----------
@app.tool()
async def ping(input: PingInput) -> CallToolResult:
    """Health check of the MCP server (no CiviCRM call)."""
    return as_text_output({"ok": True, "server": "civicrm-mcp-gdpr"})

@app.tool()
async def civicrm_create(input: CreateInput) -> CallToolResult:
    """Create a CiviCRM record for an entity"""
    payload = {
        "values": dict(input.record)
        }
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "create", payload)
    return as_text_output(out)

@app.tool()
async def civicrm_get(input: GetInput) -> CallToolResult:
    """Get one record by id (uses action=get with where=[id=...])"""
    params = {"where": [["id", "=", input.id]]} 
    if input.select: params["select"] = input.select
    if input.include: params["include"] = input.include
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "get", params)
    
    # DSGVO-Filterung anwenden
    filtered_out = GDPRFieldFilter.filter_response(input.entity, out)
    return as_text_output(filtered_out)

@app.tool()
async def civicrm_update_request(input: UpdateInput) -> CallToolResult:
    """Request update - shows current values and proposed changes, asks for confirmation"""
    
    # Get current record first
    get_payload = {"where": [["id", "=", input.id]], "limit": 1}
    async with CiviCRMClient() as cli:
        current = await cli.call(input.entity, "get", get_payload)
    
    # DSGVO-Filterung auf die aktuellen Werte anwenden
    filtered_current = GDPRFieldFilter.filter_response(input.entity, current)
    current_values = filtered_current.get("values", [{}])[0] if filtered_current.get("values") else {}
    
    # Show what will change (nur erlaubte Felder anzeigen)
    changes = {}
    for key, new_value in input.record.items():
        # Prüfen ob das Feld überhaupt angezeigt werden darf
        if GDPRFieldFilter.is_field_allowed(input.entity, key):
            old_value = current_values.get(key)
            if old_value != new_value:
                changes[key] = {"old": old_value, "new": new_value}
        else:
            # Feld ist nicht erlaubt, aber wir zeigen dass es geändert wird
            changes[key] = {"old": "[FILTERED]", "new": "[FILTERED]"}
    
    confirmation_msg = {
        "status": "confirmation_required",
        "entity": input.entity,
        "id": input.id,
        "current_record": current_values,
        "proposed_changes": changes,
        "message": f"⚠️ Ready to update {input.entity} ID {input.id}. Use civicrm_update_confirmed to proceed.",
        "_note": "Some fields may be filtered for GDPR compliance"
    }
    
    return as_text_output(confirmation_msg)


@app.tool()
async def civicrm_update_confirmed(input: UpdateInput) -> CallToolResult:
    """Execute confirmed update - ONLY use after user explicitly confirms"""
    payload = {
        "values": dict(input.record),
        "where": [["id", "=", input.id]]
    }
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "update", payload)
    return as_text_output(out)

@app.tool()
async def civicrm_delete_request(input: DeleteInput) -> CallToolResult:
    """Request deletion - shows what will be deleted and asks for confirmation"""
    
    # Get the record details first
    get_payload = {"where": [["id", "=", input.id]], "limit": 1}
    async with CiviCRMClient() as cli:
        record = await cli.call(input.entity, "get", get_payload)
    
    # DSGVO-Filterung anwenden
    filtered_record = GDPRFieldFilter.filter_response(input.entity, record)
    
    confirmation_msg = {
        "status": "confirmation_required",
        "entity": input.entity,
        "id": input.id,
        "record": filtered_record.get("values", []),
        "message": f"⚠️ Ready to delete {input.entity} ID {input.id}. Use civicrm_delete_confirmed to proceed.",
        "_note": "Record preview filtered for GDPR compliance"
    }
    
    return as_text_output(confirmation_msg)


@app.tool()
async def civicrm_delete_confirmed(input: DeleteInput) -> CallToolResult:
    """Execute confirmed deletion - ONLY use after user explicitly confirms"""
    payload = {"where": [["id", "=", input.id]]}
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "delete", payload)
    return as_text_output(out)

@app.tool()
async def civicrm_search(input: SearchInput) -> CallToolResult:
    """Generic search with where/select/include/orderBy/limit/offset"""
    params: Dict[str, Any] = {}
    if input.where is not None: params["where"] = input.where
    if input.select: params["select"] = input.select
    if input.include: params["include"] = input.include
    if input.orderBy: params["orderBy"] = input.orderBy
    if input.limit is not None: params["limit"] = input.limit
    if input.offset is not None: params["offset"] = input.offset
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "get", params)
    
    # DSGVO-Filterung anwenden
    filtered_out = GDPRFieldFilter.filter_response(input.entity, out)
    return as_text_output(filtered_out)

@app.tool()
async def civicrm_batch(input: BatchInput) -> CallToolResult:
    """Batch multiple APIv4 calls in one MCP call"""
    results = []
    async with CiviCRMClient() as cli:
        for op in input.operations:
            res = await cli.call(op.entity, op.action, op.params)
            
            # DSGVO-Filterung nur bei "get"-Operationen anwenden
            if op.action == "get":
                res = GDPRFieldFilter.filter_response(op.entity, res)
            
            results.append(res)
    return as_text_output({"results": results})

@app.tool()
async def civicrm_schema_entities(input: SchemaEntitiesInput) -> CallToolResult:
    """List available entities (cached)"""
    cached = schema_cache.get_entities()
    if cached is None:
        async with CiviCRMClient() as cli:
            out = await cli.call("Entity", "get", {"select": ["name"], "limit": 1000})
            entities = [row.get("name") for row in out.get("values", []) if row.get("name")]
            schema_cache.set_entities(entities)
    else:
        entities = cached
    return as_text_output({"entities": entities})


@app.tool()
async def civicrm_schema_fields(input: SchemaFieldsInput) -> CallToolResult:
    """List fields for an entity (cached)"""
    fields = None if input.forceRefresh else schema_cache.get_fields(input.entity)
    if fields is None:
        async with CiviCRMClient() as cli:
            out = await cli.call(input.entity, "getFields", {})
            fields = out.get("values", [])
            schema_cache.set_fields(input.entity, fields)
    return as_text_output({"entity": input.entity, "fields": fields})

@app.tool()
async def civicrm_get_actions(input: GetActionsInput) -> CallToolResult:
    """Liste alle verfügbaren Actions für eine Entity mit Details"""
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "getActions", {
            "select": ["name", "description", "params"],
            "where": [["name", "NOT IN", ["getActions", "getFields"]]]
        })
    return as_text_output(out)

@app.tool()
async def civicrm_save(input: SaveInput) -> CallToolResult:
    """Upsert records (create or update based on match criteria)"""
    params = {"records": input.records}
    if input.defaults: params["defaults"] = input.defaults
    if input.match: params["match"] = input.match
    
    async with CiviCRMClient() as cli:
        out = await cli.call(input.entity, "save", params)
    return as_text_output(out)

@app.tool()
async def civicrm_api_help(input: ApiHelpInput) -> CallToolResult:
    """Get comprehensive API documentation and available endpoints"""
    help_info = {
        "api_version": "v4",
        "explorer_url": "/civicrm/api4",
        "documentation": "https://docs.civicrm.org/dev/en/latest/api/v4/usage/",
        "common_entities": [
            "Contact", "Activity", "Contribution", "Event", 
            "Membership", "Case", "Email", "Phone", "Address"
        ],
        "common_actions": [
            "get", "create", "update", "delete", "save", 
            "getFields", "getActions", "replace"
        ],
        "where_operators": [
            "=", "!=", ">", ">=", "<", "<=",
            "LIKE", "NOT LIKE", "IN", "NOT IN",
            "BETWEEN", "NOT BETWEEN", "IS NULL", "IS NOT NULL"
        ],
        "sql_functions": [
            "COUNT(*)", "COUNT(DISTINCT field)", "SUM(field)",
            "AVG(field)", "MIN(field)", "MAX(field)",
            "GROUP_CONCAT(field)"
        ]
    }
    return as_text_output(help_info)

@app.tool()
async def civicrm_searchdisplay_run(savedSearch: str, searchDisplay = None, ctx: Context = None) -> CallToolResult:
    """Run the Saved Search with name given by parameter savedSearch. Optionally specifies the name of an associated Search Display to run. Returns results."""
    
    # Returns name of results file for rendering."""
    entity = "SearchDisplay"
    action = "run"

    params = {
        "savedSearch": savedSearch,
    }
    if searchDisplay:
        params['display'] = searchDisplay

    async with CiviCRMClient() as cli:
        saved_search_data = await cli.call("SavedSearch", "get", {
            "where": [[
                "name", "=", savedSearch
                ]]
            })
    with open('/Users/rafe/ai/civicrm_mcp_python/log.txt', 'w') as logfile:
        logfile.write(f"saved_search_data: {saved_search_data}")
    async with CiviCRMClient() as cli:
        out = await cli.call(entity, action, params)
    filtered_out = await GDPRFieldFilter.filter_searchdisplay_response(saved_search_data, out)

    return as_text_output(filtered_out)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Nimmt eine Umgebungsdatei (env_file) entgegen."
    )
    parser.add_argument(
        "--env-file", "-e",
        required=False,
        help="Pfad zur .env-Datei (z.B. /path/to/.env)"
    )
    args = parser.parse_args()

    # Nur .env laden, wenn eine Datei angegeben wurde
    if args.env_file:
        env_file = os.path.abspath(args.env_file)
        if not os.path.exists(env_file):
            print(f"Fehler: Datei nicht gefunden: {env_file}", file=sys.stderr)
            sys.exit(1)
        
        load_dotenv(env_file)
        print(f"Environment-Variablen aus {env_file} geladen", file=sys.stderr)

    # Environment-Variablen auslesen (entweder aus .env oder System)
    CIVICRM_BASE = os.environ.get('CIVICRM_BASE')
    CIVI_USER_KEY = os.environ.get('CIVI_USER_KEY')
    CIVI_SITE_KEY = os.environ.get('CIVI_SITE_KEY')
    HTTP_TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', '30'))
    LOG_FILE = os.environ.get('LOG_FILE', 'civicrm_mcp.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # stdio mode
    app.run()
