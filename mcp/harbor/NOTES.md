# Harbor 0.23.0: MCP servers, compose overlays, allowlist, job configs

Researched 2026-10-01 by reading code only. No benchmark was run.
`H` = `/home/aid1/.local/share/uv/tools/harbor/lib/python3.12/site-packages/harbor`.
`SDK` = openhands-sdk **1.50.0** sources in `scratchpad/sdk/x/openhands/sdk`. The task image pins 1.50.1. I did not have that wheel, so treat SDK line numbers as approximate.
Upstream examples were fetched from `github.com/harbor-framework/harbor` at tag `v0.23.0`. `laude-institute/harbor` now redirects to that repo.

---

## 1. MCP servers

### Schema
- `H/models/task/config.py:614`: `MCPTransport = Literal["stdio", "sse", "streamable-http"]`.
- `H/models/task/config.py:617-637`: `MCPServerConfig` has these fields:
  - `name: str`
  - `transport = "sse"` (the default is **sse**, so always set it)
  - `url` (required for sse and streamable-http)
  - `command` and `args` (for stdio)
  - `"http"` is normalized to `"streamable-http"` (`:626-629`).

### Where the servers can be declared
They are merged by name, and the agent entry wins:
- **Task:** `[environment].mcp_servers` (`H/models/task/config.py:450`). This is `[[environment.mcp_servers]]` in task.toml, as in upstream `examples/tasks/hello-mcp/task.toml`.
- **Job/agent:** `agents[].mcp_servers` (`H/models/trial/config.py:150`, field on `AgentConfig`).
- **CLI:** `--mcp-config FILE` (`H/cli/jobs.py:700`). The file is loaded by `H/cli/utils.py:179-226`, which accepts:
  - Claude-style `{"mcpServers": {name: {type,url}}}`
  - `mcp_servers: [...]`
  - `environment.mcp_servers`
  
  `type: http` becomes `streamable-http` (`:224`). The servers are appended to every agent (`H/cli/jobs.py:1521-1581`).
- **Merge:** `H/trial/trial.py:1071-1079` builds `{s.name: s for s in [*task.environment.mcp_servers, *agent.mcp_servers]}` and passes the result to the agent constructor as `mcp_servers`.
- Our tasks have `mcp_servers = []`, so the job config can add the server without editing the tasks.

### How openhands-sdk passes the servers
1. `H/agents/installed/openhands_sdk.py:238-255` serializes `self.mcp_servers` to the env var `MCP_SERVERS_JSON` as `[{name, transport, url}]` (or `command`/`args` for stdio).
2. `H/agents/installed/openhands_sdk_runner.py` (this is `/installed-agent/run_agent.py` in the container):
   - `:248-271` builds the flat dict `{name: {"url": ..., "transport": ...}}`.
   - `:274-281` passes it as `Agent(mcp_config=...)`.
   - The local file differs from `.orig` only by the PanelBench `LLM_CAPABILITY_OVERRIDES` and `LLM_NATIVE_TOOL_CALLING` patch (`:218-226`).
3. `max_iterations` becomes the `MAX_ITERATIONS` env var (`openhands_sdk.py:264-265`), which becomes `Conversation(max_iteration_per_run=...)` (`runner:286-289`).

### streamable-http support
**Yes.** The SDK's `MCPTransport = Literal["stdio","http","streamable-http","sse"]` (`SDK/mcp/config.py:494`). `MCPServer` accepts `url` and `transport` (`:497-550`) and uses fastmcp's `StreamableHttpTransport` (`SDK/mcp/utils.py:14,130`).

Timeouts:
- Tool listing at conversation start: 30 s (`SDK/conversation/impl/local_conversation.py:123`).
- Each tool call: 300 s (`SDK/mcp/tool.py:48`).

**Caveat:** if the MCP server is unreachable at startup, the SDK only logs `"MCP server startup failed ...; continuing without its tools"` and runs **without** the tools (`local_conversation.py:1388-1396`). An arm can therefore silently become A0. Check `openhands_sdk.txt` for the line `MCP servers: [...]` (runner prints it, `:298-299`), and check the tool definitions in trajectory.json.

### MCP image content
- `SDK/mcp/definition.py:60-80` converts `mcp.types.ImageContent` to SDK `ImageContent(image_urls=["data:<mime>;base64,..."])` and keeps text blocks. Other block types (for example embedded resources) are dropped with a warning.
- Secret masking leaves image blocks untouched (`SDK/mcp/tool.py:229-233`).
- The image reaches the LLM **only if `llm.vision_is_active()`** (`SDK/llm/llm.py:2732`: `not disable_vision and model_features.supports_vision`, from litellm). If vision is inactive, images are silently dropped:
  - Chat Completions path: `SDK/llm/message.py:376-380`
  - Responses API path: `SDK/llm/utils/responses_serialization.py:148-157`
  - The SDK can also auto-attach a `VisionInspectTool` for non-vision models (`SDK/agent/base.py:592`).
- Harbor's trajectory only keeps the **text** of observations (`runner:410-421`), so images returned by tools do not appear in `trajectory.json`. Log them on the gateway side instead.

---

## 2. Job-level `environment.extra_docker_compose`

### Field and CLI
- Field: `JobConfig.environment.extra_docker_compose: list[Path]`, defined in `H/models/trial/config.py` (trial `EnvironmentConfig`).
- CLI: `--extra-docker-compose FILE`, repeatable (`H/cli/jobs.py:934-941`). It is appended to the config list (`:1726-1729`).
- Config files: `harbor run -c FILE` (`run` is an alias of `harbor job start`, `H/cli/main.py:167`), or `harbor jobs start -c/--config` (`H/cli/jobs.py:412-421`).
  - The flag is repeatable. Later files deep-merge over earlier ones (`H/cli/config_sources.py:19-50`).
  - For paths listed in `_APPEND_CONFIG_PATHS` (`H/cli/jobs.py:69-88`), lists are **appended** across `-c` layers. This includes `agents`, `environment.extra_docker_compose` and `environment.extra_allowed_hosts`.
  - `harbor job schema` prints the JSON schema.
- Overlay paths are made absolute with `Path(p).expanduser().resolve()` **relative to the CWD of the harbor process** (`H/environments/base.py:244-255`). A missing file raises `FileNotFoundError`. Use absolute paths in the configs.

### Compose `-f` order
From `H/environments/docker/docker.py:351-418`:
1. resources override
2. `docker-compose-build.yaml` (or prebuilt)
3. task `environment/docker-compose.yaml`
4. **extra overlays**
5. env override
6. mounts override (`/logs`)
7. `docker-compose-egress-control.yaml`
8. generated egress-services override

Other details:
- The command is `docker compose --project-name <session_id> --project-directory <task env dir> -f ...` (`:652-667`).
- Each trial is its own compose project, so named volumes are per trial (`<project>_tool_outputs`).
- `docker compose down --rmi local --volumes` runs on cleanup (`:1105-1108`), so the volume is deleted afterwards.

### Variables available inside overlays
These come from `H/environments/docker/compose_env.py:11-27,30-52` and `docker.py:568-598`:
- `CONTEXT_DIR`: absolute task `environment/` dir (`docker.py:249`). The upstream mcp-proof example uses it the same way: `context: ${CONTEXT_DIR}/../../server`.
- `MAIN_IMAGE_NAME`, plus `PREBUILT_IMAGE_NAME` when using a prebuilt image.
- `EGRESS_CONTROL_SIDECAR_IMAGE_NAME`, `EGRESS_CONTROL_INITIAL_NETWORK_MODE` and `EGRESS_CONTROL_INITIAL_ALLOWED_HOSTS` (only when egress control is on).
- `CPUS`, `MEMORY`.
- `HOST_/ENV_{AGENT_LOGS,VERIFIER_LOGS,ARTIFACTS}_PATH`, the legacy log mounts.
- The whole host `os.environ`, plus task `[environment.env]` and persistent env. Infra variables win on collisions.

Relative paths in overlays resolve against `--project-directory`, which is the task env dir, **not** the overlay's own directory. I checked this with `docker compose config` (Compose v2.39.1): `./panels` in an overlay in another directory resolved to `<task>/environment/panels`. Still, use `${CONTEXT_DIR}/panels` because it is explicit.

### Can an overlay service mount task files and share a volume with `main`?
**Yes to both.** `docker compose config` on the real merged file stack (build, task compose, A1 overlay, egress yaml, generated egress-services override) gives:
- `panel-tools` gets the bind `<task>/environment/panels:/panels:ro`.
- `main` and `panel-tools` both mount the volume `t_tool_outputs`.
- The task's `extra_hosts` stay on the sidecar.

Caveats:
- **Do not use `build:` without `image:` for the gateway.** `down --rmi local` deletes locally built, untagged images after every trial. Also, `compose build` runs for every task, and only builds of the same environment are serialized (`docker.py:974-981`). Pre-build `panelbench-tools:v1` once, then reference it with `image:` and `pull_policy: never`.
- Do not use `expose:` or `ports:` on services that are routed through the sidecar. Under allowlist mode they run with `network_mode: service:...`, and Docker rejects port exposure in that mode. This is from Docker's documented behavior and was not tested here. The upstream mcp-proof example only works with `expose` because it runs in public mode.
- `up --detach --wait` (`docker.py:1007`, `runtime.py:37-40`) waits for the gateway healthcheck, and `main.depends_on: service_healthy` orders the startup.
- The named volume is created root-owned at the mount point unless the image has that directory. Make the gateway write files that are world-readable, or `chmod` them.

---

## 3. Agent allowlist and the egress-control sidecar

### Policy resolution
`H/trial/network_policy.py`:
- The `[agent] network_mode/allowed_hosts` in task.toml is the agent-phase policy (`:105-118`).
- Job `agents[].extra_allowed_hosts` (CLI `--allow-agent-host`, `H/cli/jobs.py:638`) is merged into it during `agent.run()` only (`:23-42,113-117`).
- `environment.extra_allowed_hosts` (CLI `--allow-environment-host`, `:812`) is merged into the `[environment]` baseline instead (`:72-88`).
- Entries must be hostnames, IPs or CIDRs, with no port or URL (`H/models/task/config.py:138-187`). A single-label name like `panel-tools` is accepted.

### Enforcement
`H/environments/docker/`:
- Egress control is enabled whenever any phase policy is not public (`docker.py:269-279`). The sidecar image is gost plus nftables (`harbor-docker-egress-control-sidecar/`).
- For each phase, `docker compose exec harbor-docker-egress-control-sidecar network-policy allow <hosts>` runs (`docker.py:1334-1358`).
- `bin/network-policy:57-84`: in the sidecar netns, every TCP connection is NAT-redirected to gost `:12345`, **except**:
  - destinations of type `fib daddr type local` (loopback and the netns's own IPs)
  - DNS to the resolv.conf nameservers
  
  Non-TCP traffic is rejected. gost (`gost.yaml`) sniffs the TLS SNI or HTTP Host and only forwards hosts in `allowlist.txt` (whitelist bypass).
- **Shared netns:** `docker.py:420-485` writes an override that gives every service from the task compose or extra overlays **without** an explicit `network_mode`/`networks` (and always `main`) the setting `network_mode: service:harbor-docker-egress-control-sidecar`, plus `depends_on` the sidecar being healthy. Those services share one network namespace (`docker.py:331-337` docstring).

### Upstream `compose-sidecar-controlled` example
Source: `examples/tasks/network-policy-matrix/static/compose-sidecar-controlled`, tag v0.23.0.
- A `helper` service with no `networks` or `network_mode` is routed through the sidecar, so it is blocked from example.com under `no-network`.
- Its twin `compose-sidecar-uncontrolled-network` declares `networks: [default]` and is left on the plain network with full internet access.
- Neither example tests main→helper traffic. That behaviour is derived from the rules above.

### What this means for `panel-tools` when `main` is on the allowlist
- **Recommended: give panel-tools no `networks`/`network_mode`, and use URL `http://127.0.0.1:8000/mcp`.**
  - main and panel-tools share the sidecar netns, so 127.0.0.1:8000 is local and the `fib daddr type local` rule accepts it. No allowlist entry is needed.
  - The gateway is also cut off from the internet (only openrouter.ai is allowed), which is good for contamination control.
  - The ports of main and the gateway must not collide. Bind 0.0.0.0:8000 or 127.0.0.1:8000.
- **`http://panel-tools:8000/mcp` will NOT work in this mode.** A service in `network_mode: service:X` has no DNS alias on the compose network, so the name does not resolve.
- **Alternative (not tested): `panel-tools` with `networks: [default]`** keeps the DNS name, so `http://panel-tools:8000/mcp` resolves through the sidecar's Docker DNS.
  - main→panel-tools is then non-local TCP, so it is redirected to gost, and gost must see `panel-tools` in the allowlist. Add it with `agents[].extra_allowed_hosts: [panel-tools]` or `allowed_hosts = ["openrouter.ai","panel-tools"]`.
  - Downside: the gateway then has **unrestricted internet**, like the uncontrolled-network example.
  - It also depends on gost matching a plain-HTTP `Host: panel-tools:8000` header against the entry `panel-tools`. Verify this with a smoke run before relying on it.

---

## 4. Job config files (`-k`, `--ak`, model, kwargs)

| CLI | Config key |
|---|---|
| `-k` | `n_attempts` |
| `-n` | `n_concurrent_trials` |
| `-o` | `jobs_dir` |
| `-a`, `-m`, `--ak k=v` | `agents: [{name, model_name, kwargs: {k: v}}]` |
| `--ae` | `agents[].env` |
| `--mcp-config` | `agents[].mcp_servers` |
| `--extra-docker-compose` | `environment.extra_docker_compose` |

Sources: `H/models/job/config.py:396-436`, `H/models/trial/config.py:63-150`. Kwargs reach the agent constructor (`H/agents/factory.py:24-35`). `OpenHandsSDKOptions` provides `max_iterations`, `reasoning_effort`, `temperature`, `load_skills` and others (`openhands_sdk.py:24-43`). `parse_kwargs` JSON-parses values, so `max_iterations=30` becomes an int (`H/cli/utils.py:111`).

**Gotchas:**
- Passing `-a` (or `--agent-import-path`) on the CLI **replaces** the config's `agents` list (`H/cli/jobs.py:1515-1556`). With `-c`, do not pass `-a`, `-m` or `--ak`.
- `--ak`, `--ae` and `--mcp-config` without `-a` are merged into every agent from the config (`:1557-1590`).
- `-p` replaces `tasks`/`datasets`. `-i` selects task names. `-o`, `-n` and `-k` override scalars.
- `agents` is appended across `-c` layers. If you layer `base.yaml` + `a1.yaml`, put `agents` in only one layer, or you get two agents.

---

## Recommended configs (A0, A1, A2 differ only in `mcp_servers` and the overlay)

`jobs/a1.yaml`:
```yaml
n_attempts: 3
n_concurrent_trials: 8
jobs_dir: jobs_mcp/a1
environment:
  type: docker
  extra_docker_compose:
    - /home/aid1/Documents/harbor/mcp/overlays/a1-panel-tools.yaml   # absolute: resolved against CWD
agents:
  - name: openhands-sdk
    model_name: openrouter/openai/gpt-5-nano
    kwargs:
      max_iterations: 30
    mcp_servers:
      - name: panelbench-tools
        transport: streamable-http        # default would be sse
        url: http://127.0.0.1:8000/mcp    # shared sidecar netns; NOT http://panel-tools:8000
```
- **A0:** the same file, without `environment.extra_docker_compose` and `mcp_servers`.
- **A2:** the same file, with its own overlay path and server name.

Run it with:
```bash
harbor run -c jobs/a1.yaml -p "$B/tasks-images" -y
```
Keep exporting `LLM_API_KEY` and `JUDGE_MODEL` as `run_nano_v024.sh` does.

`overlays/a1-panel-tools.yaml`:
```yaml
services:
  main:
    volumes:
      - tool_outputs:/workspace/tool_outputs
    depends_on:
      panel-tools:
        condition: service_healthy
  panel-tools:
    image: panelbench-tools:v1     # pre-built once; never build: here (down --rmi local)
    pull_policy: never
    # no networks/network_mode/expose/ports: Harbor routes it through the egress sidecar netns
    command: ["python", "-m", "panel_tools.server", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]
    volumes:
      - ${CONTEXT_DIR}/panels:/panels:ro
      - tool_outputs:/workspace/tool_outputs
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('127.0.0.1',8000),2).close()"]
      interval: 2s
      timeout: 5s
      retries: 60
      start_period: 5s
volumes:
  tool_outputs: {}
```
No `extra_allowed_hosts` is needed for this layout. Verify it in the smoke run:
- `openhands_sdk.txt` shows `MCP servers: ['panelbench-tools']`.
- The trajectory's `tool_definitions` include the gateway tools.
- The gateway log shows the calls.
- Optionally, run `network-policy show` inside the sidecar.

Fallback if localhost cannot be used: give `panel-tools` `networks: [default]` and URL `http://panel-tools:8000/mcp`, and add `agents[0].extra_allowed_hosts: [panel-tools]`. This is untested, and the gateway then has open egress.
