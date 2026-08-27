# Using this template

This repository was created using `gw-plugin-template`. This provides a basic but functional structure to demonstrate how to fulfil all required Groundworkers plugin contracts.

The steps below rename the placeholder package, set out what to keep and what to remove, and cover the repository configuration a template cannot carry with it. This file and `scripts/bootstrap.py` remove themselves once step 1 completes.

## What the template copies

GitHub's "Use this template" copies the files on `main` into a new repository and begins the history fresh. There is no fork relationship and no upstream, so later changes to the template do not propagate here.

Every file is copied, including the workflows, the issue and pull request templates, the git hook and the whole `src/` tree. Repository settings are not: labels, branch protection, environments, secrets, the repository description and topics all start empty.

GitHub performs no substitution, so the placeholder name remains in the distribution name, the `src/` directory, the wheel packages path, both entry points, `config.tool_name`, `plugin.name`, every tool name, the PyPI URL in `publish.yml`, the tests and the README. Step 1 resolves all of them together.

## 1. Rename the package

```bash
python3 scripts/bootstrap.py my-new-plugin --description "What this plugin does."
```

Pass `--dry-run` to list the files that would change without modifying them. The script replaces `gw_plugin_template` with `my_new_plugin`, `gw-plugin-template` with `my-new-plugin` and `GwPluginTemplate` with `MyNewPlugin`, renames the package directory, then deletes itself and this file. It depends only on the standard library and can be run before `uv sync`.

Confirm the repository is green before altering any behaviour:

```bash
uv sync --all-extras --dev
uv run ruff check . && uv run ty check src/ && uv run pytest -q
```

## 2. Replace the example

The example plugin performs lookups against a small catalogue file. Replace it with your own implementation, preserving the separation between layers: `adapters` holds anything that reaches a database, file or network; `service` holds behaviour and imports no server types; `tools` is the only module aware of MCP; `plugin` composes the three and presents them to Groundworkers.

Most of the contract is optional, and the example exercises more of it than a typical plugin requires. The following can be removed:

| Surface | Safe to remove when |
| --- | --- |
| `setup_steps` on the plugin, and `setup_cli.py` | The plugin has no data to prepare before it can answer a question. |
| `tui_workflow` | Almost always. Returning `None`, as the template does, directs Groundworkers to derive the configuration page from the schema. Implement it only where configuration requires live lookups or conditional branching. |
| `verify_readiness`, its counterpart on the service, and the `*_status` tool | Operators have no reason to distinguish "configured" from "working". This is rarer than it appears. |
| `api_token` in `config.py` | The plugin owns no secret. A `RefTo` field is preferable in most cases, since sensitivity is then declared once, on the referenced schema. |
| `catalogue_db` in `config.py` | The CDM connection Groundworkers has already resolved is sufficient. |
| `paths.py` | No configured value is a path that should resolve relative to the config file. |

Retain `tests/test_plugin_contract.py`. These assertions appear trivial, but they detect the two errors that otherwise present as a plugin which installs correctly and then does nothing: an entry point resolving to a class rather than a constructed instance, and `plugin.name` diverging from `Config.tool_name`.

The Groundworkers documentation covers the reasoning behind each surface under Development and architecture, on the plugin architecture page.

## 3. Configure the repository

The template ships continuous integration that runs `ruff`, `ty` and `pytest` on every pull request, and a publish workflow that builds and uploads a wheel when a tag is pushed. Two pieces of repository configuration apply regardless of how your project is governed:

- Branch protection on `main`, requiring a pull request and a passing build.
- If the package will be published: a GitHub environment named `pypi`, and a PyPI trusted publisher for workflow `publish.yml` in that environment.

Everything beyond that is the convention of the repository's owning organisation, and is contained entirely within `.github/`.

### Australian Cancer Data Network repositories

The shipped workflows call reusable workflows from [cava-devops](https://australiancancerdatanetwork.github.io/cava-devops/), which additionally require exactly one of `breaking`, `feature`, `fix`, `dependencies` or `chore` on every pull request, and use that label to draft the release and resolve the version bump. The canonical label set and the standard branch ruleset are therefore prerequisites. The [setup guide](https://australiancancerdatanetwork.github.io/cava-devops/guides/setup-new-repo/) covers the full checklist; the two steps most often missed are:

```bash
# From a cava-devops checkout:
scripts/bootstrap-labels.sh AustralianCancerDataNetwork/my-new-plugin

gh api -X PUT repos/AustralianCancerDataNetwork/my-new-plugin/environments/pypi
```

### Everywhere else

Delete `.github/workflows/`, `.github/release-drafter.yml`, `.github/CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/`, then add whatever continuous integration you use. Nothing outside `.github/` depends on any of it, and the commands in the Development section of the README are the whole of what CI needs to run.

`.githooks/pre-commit` is worth keeping either way. It keeps `uv.lock` in step with `pyproject.toml` when a dependency changes, and is independent of any CI system. Enabling it is a per-clone setting that is not committed, so each contributor runs it once:

```bash
git config core.hooksPath .githooks
```

## Expected behaviour that can resemble a fault

The version reads as something like `0.1.dev3+g1a2b3c4`. `hatch-vcs` derives the version from git tags, and a new repository has none. The first release creates the first tag, after which the version is ordinary. Do not reintroduce a static `version =` into `pyproject.toml`.

`groundworkers` is pinned to a git branch under `[tool.uv.sources]`. The `groundworkers.plugins` entry-point group currently exists only on the `plugins` branch; the published 0.4.0 installs a plugin without error and then never loads it. Treat the pin as a release blocker: uv sources are not recorded in wheel metadata, so a release made while it remains would resolve back to the broken 0.4.0. Remove the pin and raise the dependency to `groundworkers>=0.5,<1` once that release ships.

## Improving the template

The template is an ordinary repository and can be changed through a pull request like any other. Generated repositories hold no reference back to it, so a change reaches only plugins created afterwards. Where a correction also applies to existing plugins, apply it to them directly.
