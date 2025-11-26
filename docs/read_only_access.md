# Allowing Read-Only Access to CiviCRM

To remove a tool from the MCP server, simply remove the `@app.tool()` decorator preceding the function in `app.py`. Or alternatively, delete the function altogether.

For example, to remove the Create tool:

```python
@app.tool()
async def civicrm_create(input: CreateInput, ctx: Context = None) -> CallToolResult:
```

becomes

```python
# @app.tool()
async def civicrm_create(input: CreateInput, ctx: Context = None) -> CallToolResult:
```

To completely disable the LLM's ability to create, modify, or delete records, repeat the above with the following functions in `app.py`:

- `civicrm_create`
- `civicrm_update_request`
- `civicrm_update_confirmed`
- `civicrm_delete_request`
- `civicrm_delete_confirmed`
- `civicrm_batch`
- `civicrm_save`