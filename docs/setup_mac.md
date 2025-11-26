# Setup Instructions for Mac (English)

The [civicrm_mcp_python](https://github.com/Stewie23/civicrm_mcp_python#) repository sets up an MCP server for CiviCRM APIv4 that works with Claude Desktop.

- [Setup](#setup)
  - [Python](#python)
  - [Environment](#environment)
  - [Claude](#claude)
- [Using the MCP Server](#using-the-mcp-server)
- [Notes](#notes)
  - [Authentication](#authentication)
  - [Claude Configuration](#claude-configuration)

## Setup

### Python

- Install Python 
    - e.g., using Homebrew: https://docs.brew.sh/Homebrew-and-Python
    - for convenience, you may want to install `python-is-python3` to use `python` instead of `python3` and `pip` instead of `pip3` for the commands below, or do something like `alias python='python3'`
- Clone the repository

```bash
git clone git@github.com:Stewie23/civicrm_mcp_python.git
```

### Environment

- Set up virtual environment and install requirements

```bash
cd civicrm_mcp_python 
python3 -m venv .venv               ## create environment
source .venv/bin/activate           ## source environment
pip3 install -r requirements.txt    ## install packages
```

- There should now be a `.venv` folder in your `civicrm_mcp_python` working directory (`ls -a`)
- Once sourced, there should be `(.venv)` that appears before each line in your terminal
- Create `.env` file:

```
CIVI_URL=https://website-base-url-goes-here/civicrm/api4
AUTH_SCHEME=bearer
CIVI_TOKEN=user_api_token
```

- In some cases, `CIVI_URL` should be `https://website-base-url-goes-here/civicrm/ajax/api4`
- See [Notes](#api-key-method) for details on the API key

### Claude

- Complete the Claude desktop installation instructions from: https://support.claude.com/en/articles/10065433-installing-claude-desktop
- Add the following to the Claude config file, located at `~/Library/Application Support/Claude/claude_desktop_config.json`
> alternatively, navigate to the file via Claude > Settings > Developer > Edit Config

```json
"mcpServers": {
  "civicrm": {
    "command": "/full/path/to/civicrm_mcp_python/.venv/bin/python3",
    "args": [
      "/full/path/to/civicrm_mcp_python/app.py"
    ],
    "env": {
      "CIVI_URL": same as above,
      "AUTH_SCHEME": same as above,
      "CIVI_TOKEN": same as above,
      "CIVI_USER_KEY": user API key,
      "CIVI_SITE_KEY": site API key
    }
  }
}
```

## Using the MCP server

Refer to the repo’s `README` for the available tools.

### Check connection using `ping`

Ask the LLM to ping CiviCRM. It should return a success message if the MCP server and CiviCRM site are connected.

Details

- the request should look something like:

```bash
{
  `input`: {}
}
```

- the response should look something like:

```json
{
    "ok": true,
  "server": "civicrm-mcp-python"
}
```

## Notes

### Authentication

The LLM must be able to authenticate with the Civi site. There are multiple ways to do this. The instructions above use API keys.

#### API Key Method

- The easiest way to find/generate API keys is with the API Key extension: https://docs.civicrm.org/sysadmin/en/latest/setup/api-keys/
- Navigate to the “API Key” tab of a contact (ideally, the admin) and copy the API keys from there

#### JWT Bearer Token Method

- Generate a token for the site using the following code

```php
$token = Civi::service('crypto.jwt')->encode([
    'exp' => time() + 60*60,      // Expires in 60 minutes
    'sub' => 'cid:203',             // Subject (contact ID)
    'scope' => 'authx',             // Allow general authentication
]);
```

### Claude Configuration

- Some links that may be helpful:
    - https://www.youtube.com/watch?v=zw6pxv0hvXY
    - https://modelcontextprotocol.io/docs/develop/connect-local-servers
    - https://docs.civicrm.org/dev/en/latest/api/v4/rest/
    - https://docs.civicrm.org/sysadmin/en/latest/setup/api-keys/
