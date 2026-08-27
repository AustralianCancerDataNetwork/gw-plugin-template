# Using this template

> This file documents the template itself. `scripts/bootstrap.py` deletes it,
> along with itself, once you have run it.

## What "Use this template" does

Pressing **Use this template** on GitHub copies the files on `main` into a new
repository with a single fresh commit. There is no fork link and no upstream, so
the new repo never receives later changes made here.

**Files come across.** `.github/workflows/`, the issue and PR templates,
`.githooks/`, the whole `src/` tree.

**Repository settings do not.** Labels, the branch ruleset, the `pypi`
environment, secrets, the PyPI trusted publisher, the description and topics all
start empty. Step 3 below is not optional.

**Nothing is substituted.** GitHub does no templating. The placeholder name
appears in the distribution name, the `src/` directory, the wheel packages path,
two entry points, `config.tool_name`, `plugin.name`, every tool name, the PyPI
URL in `publish.yml`, the tests, and the README. That is what step 1 is for.

## 1. Rename it

```bash
python3 scripts/bootstrap.py my-new-plugin --description "What this plugin does."
```

Add `--dry-run` first if you want to see the file list. The script rewrites
`gw_plugin_template` → `my_new_plugin`, `gw-plugin-template` → `my-new-plugin`
and `GwPluginTemplate` → `MyNewPlugin`, renames `src/`, then deletes itself and
this file. It is stdlib-only, so it runs before `uv sync`.

Then confirm the repo is green before you change any behaviour:

```bash
uv sync --all-extras --dev
uv run ruff check . && uv run ty check src/ && uv run pytest -q
git config core.hooksPath .githooks
```

## 2. Make it your plugin

The example is a catalogue lookup. Replace it, keeping the layering: `adapters`
does I/O, `service` holds behaviour with no server types, `tools` is the only
module that imports MCP concepts, `plugin` wires them together.

Delete what you do not need — each is independently optional:

| Surface | Delete if |
| --- | --- |
| `setup_steps` on the plugin, and `setup_cli.py` | The plugin needs no data preparation. |
| `tui_workflow` | Always, unless your config needs live discovery or branching. Returning `None` (the default) is the correct answer for plain scalar and `RefTo` fields. |
| `verify_readiness`, `service.verify_readiness`, `*_status` tool | Operators never need to tell "configured" from "actually usable". Usually they do — keep it. |
| `api_token` in `config.py` | The plugin owns no secret of its own. Prefer a `RefTo` so sensitivity stays declared on the referenced schema. |
| `catalogue_db` in `config.py` | The shared CDM connection on `PluginContext` is enough. |
| `paths.py` | No configured path resolves relative to the config file. |

Keep `tests/test_plugin_contract.py`. Those assertions catch the wiring mistakes
that otherwise fail silently at host startup: an entry point pointing at a class
instead of a built instance, and `plugin.name` drifting from
`Config.tool_name`, which Groundworkers rejects at startup.

The full design rationale for each surface is in the Groundworkers docs, under
Development and architecture → Plugin architecture.

## 3. Apply the repository settings

None of this is copied by the template. Run it against the new repo:

```bash
# From a cava-devops checkout:
scripts/bootstrap-labels.sh AustralianCancerDataNetwork/my-new-plugin

# The pypi environment publish.yml deploys into:
gh api -X PUT repos/AustralianCancerDataNetwork/my-new-plugin/environments/pypi

# Squash-only merges, with the PR title as the commit message:
gh api -X PATCH repos/AustralianCancerDataNetwork/my-new-plugin \
  -F allow_merge_commit=false -F allow_rebase_merge=false -F allow_squash_merge=true \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=BLANK
```

Then add the branch ruleset on `main` (1 approval, linear history, force pushes
and deletion blocked, required checks `label-gate / check` and
`build-test / test`, admin bypass) and a pending PyPI trusted publisher for
workflow `publish.yml` in environment `pypi`. Both are described in the
[cava-devops setup guide](https://australiancancerdatanetwork.github.io/cava-devops/guides/setup-new-repo/).

## 4. Two things that will look wrong and are not

**The version is `0.1.devN+g<sha>`.** `hatch-vcs` derives the version from git
tags and a fresh repo has none. The first release creates the first tag. Do not
add a static `version =` to `pyproject.toml`.

**`groundworkers` is pinned to a git branch.** The `groundworkers.plugins`
entry-point group exists only on the `plugins` branch; published 0.4.0 installs
a plugin and silently never loads it. The pin in `[tool.uv.sources]` is a
release blocker: uv sources are not recorded in wheel metadata, so a release
made while it is in place would resolve to a broken 0.4.0. Drop the pin and
raise the dependency to `groundworkers>=0.5,<1` once that release ships.

## Keeping this template current

This repo is a normal repo: change it with a labelled PR like any other. Because
generated repos have no upstream link, a change here reaches only plugins
created after it. If a fix matters to existing plugins, apply it to them
directly.
