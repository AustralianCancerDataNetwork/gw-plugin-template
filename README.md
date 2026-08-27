# Groundworkers Plugin Template

Template for a Groundworkers plugin.

A Groundworkers plugin is a separate package that adds tools to the Groundworkers MCP server without Groundworkers knowing anything about it. You register one object under the `groundworkers.plugins` entry-point group, and at startup the host finds it, resolves whatever configuration it declared, builds it, and lets it register its tools against the shared server.

```toml
[project.entry-points."groundworkers.plugins"]
gw_plugin_template = "gw_plugin_template.plugin:plugin"
```

## Tools

| Tool | What it does |
| --- | --- |
| `gw_plugin_template_list` | Lists the catalogue entries this plugin publishes. |
| `gw_plugin_template_search` | Finds entries whose key, label or description matches a term. |
| `gw_plugin_template_status` | Returns the same readiness report the setup console shows. |

Tool names share one namespace with the host and every other installed plugin, which is why they all start with the plugin name.

## Configuration

Settings live under `[tools.gw_plugin_template]` in the stack config file. Everything is optional, and the plugin will start and tell you what's missing rather than refusing to load.

```toml
[tools.gw_plugin_template]
catalogue_path = "./catalogue.json"   # relative paths resolve against this file
default_limit = 10
# catalogue_db = "my_db"              # a reference to an entry configured elsewhere
# api_token = "..."                   # declared sensitive, so it's redacted everywhere
```

`catalogue_db` is a `RefTo` field, which means it holds the name of a database entry the operator has already set up rather than a host, port and password of its own. That's usually the right way to reach a database from a plugin, since the credentials stay declared on the connection they belong to. `api_token` shows the other case: a secret the plugin genuinely owns, marked `Sensitive()` so configuration views, review diffs and logs redact it.

You can fill both in by hand, or run `omop-config` or the Groundworkers setup console and let it build the form from the schema.

## Setup

The plugin adds one step, **Refresh catalogue**, to the Groundworkers setup console. Choosing it runs `python -m gw_plugin_template.setup_cli refresh` as a separate process through the host's maintenance-run store, so progress, logs, cancellation and retry work the same way they do for Groundworkers' own operations.

You can run the same command yourself:

```bash
OA_CONFIG_PATH=/path/to/config.toml \
  python -m gw_plugin_template.setup_cli refresh --source my-source
```

## How the package is laid out

| Module | What lives there |
| --- | --- |
| `config.py` | The settings class. Its `tool_name` has to match `plugin.name`. |
| `adapters.py` | Anything that touches a database, a file or the network. |
| `service.py` | The actual behaviour. No MCP or server types, so you can test it by calling it. |
| `tools.py` | The MCP surface, and the only module that knows a server exists. |
| `plugin.py` | Where it all comes together: `name`, `config_cls`, `build`, `register`, and the optional `setup_steps`, `verify_readiness` and `tui_workflow`. |
| `setup_cli.py` | Slow work, run out of process by the host. |
| `paths.py` | Resolves a configured relative path against the config file. |

`build()` can return `None` when something the plugin can't work without is missing. Groundworkers then skips it, carries on serving everything else, and reports why. It's usually better to build anyway and let `verify_readiness` explain the problem, so the operator can see what to fix instead of watching the plugin vanish.

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run ty check src/
uv run pytest -q
```

The `uv.lock` sync hook needs enabling once per clone:

```bash
git config core.hooksPath .githooks
```

## Versioning and releases

Versions come from git tags via [`hatch-vcs`](https://github.com/ofek/hatch-vcs), so there's no version string anywhere in the source and no `CHANGELOG.md`. The release history lives in GitHub Releases, which `release-drafter` keeps up to date as PRs merge.

Every PR into `main` needs exactly one of `breaking`, `feature`, `fix`, `dependencies` or `chore`, and that label decides both the changelog section and the version bump. The [cava-devops PR workflow](https://australiancancerdatanetwork.github.io/cava-devops/guides/pr-workflow/) has the details.

Contribution and labelling rules are in [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md).
