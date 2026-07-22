# Real captured output — what actually happened when I ran this

I ran `demo/cocoindex_demo.py`'s steps live, for real, before handing you this
project. This file is the unedited transcript. I'm including it because my
sandbox's network is restricted to a small allowlist (pypi.org, npmjs.com,
github.com, etc.) and does **not** include `huggingface.co` — which is where
cocoindex-code downloads its embedding model from on first run. So the
semantic *search* step failed here with a network error. Everything else —
installing the tool, the CLI, the full MCP protocol handshake, the tool
schema — is real and worked.

On your machine, with normal internet access, `ccc init` + `ccc index` will
successfully download the embedding model (~22MB, `Snowflake/snowflake-arctic-embed-xs`
by default) and `search` will return real ranked results instead of the error
below.

## Install

```
$ uv tool install --force "cocoindex-code[full]"
Installed 2 executables: ccc, cocoindex-code
```

## Step 1-2: `ccc init -f` + `ccc index`

```
$ ccc init -f
Created user settings: /root/.cocoindex_code/global_settings.yml

Applied recommended defaults for Snowflake/snowflake-arctic-embed-xs:
  indexing_params: {}
  query_params:    {'prompt_name': 'query'}

Testing embedding model: sentence-transformers / Snowflake/snowflake-arctic-embed-xs

  [FAIL] Model Check (indexing)
    ERROR: OSError: We couldn't connect to 'https://huggingface.co' to load the
    files, and couldn't find them in the cached files. Check your internet
    connection or see how to run the library in offline mode.

Created project settings: /home/claude/demo_project/.cocoindex_code/settings.yml
Run `ccc index` to build the index.

$ ccc index
Indexing failed: We couldn't connect to 'https://huggingface.co' to load the
files, and couldn't find them in the cached files.
```

This is a **sandbox network limitation, not a bug in cocoindex-code** — the
tool did exactly what it should: tried to fetch the embedding model, failed
because the host was unreachable, and reported the failure clearly.

## Step 3: MCP handshake — `ccc mcp` over stdio

This part needs no embedding model, just the server starting up. Real,
successful output:

```json
==> initialize
{}

<== initialize result
{
  "protocolVersion": "2025-11-25",
  "capabilities": {
    "prompts": {"listChanged": false},
    "resources": {"subscribe": false, "listChanged": false},
    "tools": {"listChanged": false}
  },
  "serverInfo": {
    "name": "cocoindex-code",
    "version": "1.28.1"
  },
  "instructions": "Code search and codebase understanding tools.\nUse when you need to find code, understand how something works, locate implementations, or explore an unfamiliar codebase.\nProvides semantic search that understands meaning -- unlike grep or text matching, it finds relevant code even when exact keywords are unknown."
}
```

## Step 4: `tools/list`

```json
<== tools/list result
[
  {
    "name": "search",
    "description": "Semantic code search across the entire codebase -- finds code by meaning, not just text matching. Use this instead of grep/glob when you need to find implementations, understand how features work, or locate related code without knowing exact names or keywords. Accepts natural language queries (e.g., 'authentication logic', 'database connection handling') or code snippets. Returns matching code chunks with file paths, line numbers, and relevance scores.",
    "inputSchema": {
      "properties": {
        "query": {"type": "string", "description": "Natural language query or code snippet to search for."},
        "limit": {"type": "integer", "default": 5, "minimum": 1, "maximum": 100},
        "offset": {"type": "integer", "default": 0},
        "refresh_index": {"type": "boolean", "default": true},
        "languages": {"type": ["array", "null"]},
        "paths": {"type": ["array", "null"]}
      },
      "required": ["query"]
    }
  }
]
```

## Step 5: `tools/call search` — real request, real (failed) response

```json
==> tools/call search
{
  "query": "function that verifies a user's password",
  "limit": 3
}

<== tools/call search result
{
  "success": false,
  "results": [],
  "total_returned": 0,
  "offset": 0,
  "message": "Query failed: Daemon error: We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them in the cached files."
}
```

Same network limitation as step 1-2 — the search tool works, but it can't
embed the query without the model.

## Bonus: `ccc grep` — the one command that needs no index or embedding model

This one worked end-to-end, live, in the sandbox:

```
$ ccc grep "def verify_user"
auth.py
9| def verify_user(username, password, stored_hash):
```

`ccc grep` does structural, example-based matching (like an AST-aware grep)
without touching the embedding pipeline at all — worth knowing about as a
fast fallback even inside a semantic-first workflow.

## What to expect when you run `demo/cocoindex_demo.py` yourself

With real internet access, step 1-2 will finish successfully (downloading
the ~22MB model), and step 5's `search` calls will return actual ranked
results — something like:

```json
{
  "success": true,
  "results": [
    {
      "file_path": "auth.py",
      "line_start": 9,
      "line_end": 10,
      "name": "verify_user",
      "chunk_type": "function",
      "score": 0.81,
      "content": "def verify_user(username, password, stored_hash):\n    return hash_password(password) == stored_hash"
    }
  ],
  "total_returned": 1
}
```

If your results differ in exact score or ranking, that's expected — it
depends on the embedding model and index state, not a sign anything is wrong.
