# Groundworkers Plugin Template

Template for a Groundworkers plugin.

This plugin registers itself under the `groundworkers.plugins` entry-point group. Groundworkers discovers it at startup, resolves its configuration, builds its service, and registers its MCP tools against the one shared server. Nothing in Groundworkers imports this package by name.

```toml
[project.entry-points."groundworkers.plugins"]
gw_plugin_template = "gw_plugin_template.plugin:plugin"
```

## Tools

| Tool | Purpose |
| --- | --- |
| `gw_plugin_template_list` | List catalogue entries published by this plugin. |
| `gw_plugin_template_search` | Find entries whose key, label or description matches a term. |
| `gw_plugin_template_status` | Return the readiness report the setup console shows. |

## Configuration

Settings live under `[tools.gw_plugin_template]` in the stack config file. Every field is optional; the plugin loads and explains itself when nothing is set.

```toml
[tools.gw_plugin_template]
catalogue_path = "./catalogue.json"   # relative paths resolve against this file
default_limit = 10
# catalogue_db = "my_db"              # a RefTo an entry configured elsewhere
# api_token = "..."                   # declared Sensitive; redacted everywhere
```

`catalogue_db` and `api_token` are unset by default. Prefer a `RefTo` field over re-declaring host, port and credentials: the plugin stores only the logical reference name and sensitivity stays declared on the referenced schema.

Run `omop-config` or the Groundworkers setup console to configure it interactively; the page is derived from the schema, so no Groundskeeping-aware code is needed here.

## Setup

The plugin publishes one setup step, **Refresh catalogue**, in the Groundworkers setup console. It runs `python -m gw_plugin_template.setup_cli refresh` out of process through the host's durable maintenance-run store, so logs, progress, cancellation and retry are shared with core operations.

```bash
OA_CONFIG_PATH=/path/to/config.toml \
  python -m gw_plugin_template.setup_cli refresh --source my-source
```

## Layout

| Module | Responsibility |
| --- | --- |
| `config.py` | The `PackageConfigBase` subclass. `tool_name` must equal `plugin.name`. |
| `adapters.py` | Everything that touches a database, file or network. |
| `service.py` | Behaviour, with no MCP or server types. Testable by calling methods. |
| `tools.py` | The MCP surface. The only module that knows about a server. |
| `plugin.py` | Composition root: `name`, `config_cls`, `build`, `register`, plus the optional `setup_steps`, `verify_readiness` and `tui_workflow`. |
| `setup_cli.py` | Long-running work, run out of process by the host. |
| `paths.py` | Resolves a configured relative path against the config file. |

`build()` returns `None` when a prerequisite the plugin cannot work without is missing; `register()` is then never called and Groundworkers keeps serving its core capabilities. Prefer a degraded-but-explainable state over `None` whenever the plugin can still describe its own problem — that is what `verify_readiness` is for.

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run ty check src/
uv run pytest -q
```

Enable the `uv.lock` sync hook once per clone:

```bash
git config core.hooksPath .githooks
```

## Versioning and releases

The version is derived from git tags by [`hatch-vcs`](https://github.com/ofek/hatch-vcs); there is no version string in any source file and there is no `CHANGELOG.md`. The release history lives in GitHub Releases, drafted by `release-drafter` as PRs merge.

Every pull request against `main` must carry exactly one of `breaking`, `feature`, `fix`, `dependencies`, or `chore`. See the [cava-devops PR workflow](https://australiancancerdatanetwork.github.io/cava-devops/guides/pr-workflow/).

Contribution and labelling rules are in [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).
