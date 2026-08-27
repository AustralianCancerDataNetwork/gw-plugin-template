# Groundworkers Plugin Template

Template for a Groundworkers plugin.

A Groundworkers plugin is a separately installed package that adds tools to the Groundworkers MCP server without Groundworkers importing it by name. The package registers one constructed object under the `groundworkers.plugins` entry-point group. At startup the host discovers that object, resolves the configuration it declares, builds it, and allows it to register its tools against the shared server.

```toml
[project.entry-points."groundworkers.plugins"]
gw_plugin_template = "gw_plugin_template.plugin:plugin"
```

## Tools

| Tool | Purpose |
| --- | --- |
| `gw_plugin_template_list` | Lists the catalogue entries this plugin publishes. |
| `gw_plugin_template_search` | Finds entries whose key, label or description matches a term. |
| `gw_plugin_template_status` | Returns the readiness report also shown in the setup console. |

Tool names share a single namespace with the host and every other installed plugin, which is why each is prefixed with the plugin name.

## Configuration

Settings are read from `[tools.gw_plugin_template]` in the stack config file. Every field is optional; where something is missing the plugin still loads and reports the omission rather than refusing to start.

```toml
[tools.gw_plugin_template]
catalogue_path = "./catalogue.json"   # relative paths resolve against this file
default_limit = 10
# catalogue_db = "my_db"              # a reference to an entry configured elsewhere
# api_token = "..."                   # declared sensitive, and redacted everywhere
```

`catalogue_db` is a `RefTo` field, holding the name of a database entry an operator has already configured rather than a host, port and password of its own. This is the preferred way for a plugin to reach a database, because credentials remain declared on the connection they belong to. `api_token` covers the other case, a secret the plugin itself owns, marked `Sensitive()` so that configuration views, review diffs and log records redact it.

Values can be set by hand, or through `omop-config` and the Groundworkers setup console, which derive the form from the schema.

## Setup

The plugin contributes one step, **Refresh catalogue**, to the Groundworkers setup console. Selecting it runs `python -m gw_plugin_template.setup_cli refresh` as a separate process through the host's maintenance-run store, so progress, logs, cancellation and retry behave as they do for the host's own operations.

The same command can be run directly:

```bash
OA_CONFIG_PATH=/path/to/config.toml \
  python -m gw_plugin_template.setup_cli refresh --source my-source
```

## Package layout

| Module | Responsibility |
| --- | --- |
| `config.py` | The settings class. Its `tool_name` must match `plugin.name`. |
| `adapters.py` | Anything that reaches a database, a file or the network. |
| `service.py` | Behaviour, importing no MCP or server types, and testable by direct call. |
| `tools.py` | The MCP surface, and the only module aware that a server exists. |
| `plugin.py` | Composition: `name`, `config_cls`, `build`, `register`, and the optional `setup_steps`, `verify_readiness` and `tui_workflow`. |
| `setup_cli.py` | Long-running work, run out of process by the host. |
| `paths.py` | Resolves a configured relative path against the config file. |

`build()` may return `None` where a prerequisite the plugin cannot operate without is absent. Groundworkers then skips the plugin, continues serving everything else, and reports the reason. Building anyway and letting `verify_readiness` describe the problem is usually preferable, since an operator can then see what to correct rather than finding the plugin missing.

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run ty check src/
uv run pytest -q
```

`.githooks/pre-commit` keeps `uv.lock` in step with `pyproject.toml` when a dependency changes. Enabling it is a per-clone setting and is not committed:

```bash
git config core.hooksPath .githooks
```

## Versioning and releases

Versions are derived from git tags by [`hatch-vcs`](https://github.com/ofek/hatch-vcs), so no version string appears in the source and there is no `CHANGELOG.md`. The release history lives in GitHub Releases.

The workflows in `.github/` implement the [cava-devops](https://australiancancerdatanetwork.github.io/cava-devops/) conventions, under which each pull request into `main` carries exactly one of `breaking`, `feature`, `fix`, `dependencies` or `chore`, and that label determines both the changelog section and the version bump. Projects outside that organisation can replace the contents of `.github/` with their own continuous integration; nothing elsewhere in the package depends on it.

Contribution and labelling rules are in [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).
