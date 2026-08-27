# Using this template

You're looking at a fresh repo made from `gw-plugin-template`. What's here is a small but complete Groundworkers plugin, already wired into the shared CAVA CI/CD, so you can start on your own code instead of picking bits out of an existing plugin and hoping you got all of them.

Work through the three steps below and you'll have a working, releasable plugin repo. This file and the bootstrap script delete themselves along the way, so nothing template-shaped survives into your project.

## What you actually got

GitHub's "Use this template" button copies the files on `main` into a new repository and starts the history fresh. There's no fork relationship and no upstream, so later changes to the template won't find their way here.

The files all came across: the workflows, the issue and PR templates, the git hook, the whole `src/` tree.

Repository *settings* did not. Labels, the branch ruleset, the `pypi` environment, secrets, the PyPI trusted publisher, the repo description and topics all start out empty. Step 3 is where you fill them in.

GitHub also doesn't substitute anything, so the placeholder name is still sitting in the distribution name, the `src/` directory, the wheel packages path, both entry points, `config.tool_name`, `plugin.name`, every tool name, the PyPI URL in `publish.yml`, the tests and the README. Step 1 deals with all of that in one go.

## 1. Rename it

```bash
python3 scripts/bootstrap.py my-new-plugin --description "What this plugin does."
```

Pass `--dry-run` first if you'd like to see which files it touches. The script swaps `gw_plugin_template` for `my_new_plugin`, `gw-plugin-template` for `my-new-plugin` and `GwPluginTemplate` for `MyNewPlugin`, renames the package directory, and then removes itself and this file. It only uses the standard library, so you can run it before `uv sync`.

Check that everything still passes before you start changing behaviour:

```bash
uv sync --all-extras --dev
uv run ruff check . && uv run ty check src/ && uv run pytest -q
git config core.hooksPath .githooks
```

That last line is a per-clone setting that isn't committed, so everyone who clones the repo needs to run it once. It keeps `uv.lock` in step with `pyproject.toml` when you edit dependencies.

## 2. Make it your plugin

The example plugin looks things up in a small catalogue file. Swap that out for whatever yours does, and try to keep the layering as you go: `adapters` is where anything touches a database, file or network; `service` holds the actual behaviour and knows nothing about servers; `tools` is the one module that talks to MCP; `plugin` ties the three together and hands them to Groundworkers.

Most of the plugin contract is optional, and the example uses more of it than a typical plugin needs. Here's what you can throw away:

| Surface | Safe to remove when |
| --- | --- |
| `setup_steps` on the plugin, and `setup_cli.py` | Your plugin has no data to prepare before it can answer questions. |
| `tui_workflow` | Almost always. Returning `None`, which is what the template does, tells Groundworkers to build the config page from your schema. Write a real one only if configuring your plugin needs live lookups or branching. |
| `verify_readiness`, its counterpart on the service, and the `*_status` tool | Operators would never need to tell "configured" from "actually working". That's rarer than it sounds, so think twice here. |
| `api_token` in `config.py` | Your plugin holds no secret of its own. A `RefTo` field is usually better anyway, since sensitivity is then declared once on the thing being referenced. |
| `catalogue_db` in `config.py` | The CDM connection Groundworkers already resolved for you is enough. |
| `paths.py` | Nothing in your config is a path that should resolve relative to the config file. |

One thing to hold on to is `tests/test_plugin_contract.py`. Those tests look trivial, but they catch the two mistakes that otherwise show up as a plugin that installs cleanly and then quietly does nothing: an entry point pointing at a class rather than a built instance, and `plugin.name` drifting away from `Config.tool_name`.

If you want the reasoning behind any part of the contract, the Groundworkers docs cover it under Development and architecture, in the plugin architecture page.

## 3. Apply the repository settings

These are the ones the template couldn't bring with it. Run them against your new repo:

```bash
# From a cava-devops checkout:
scripts/bootstrap-labels.sh AustralianCancerDataNetwork/my-new-plugin

# The pypi environment that publish.yml deploys into:
gh api -X PUT repos/AustralianCancerDataNetwork/my-new-plugin/environments/pypi

# Squash-only merges, using the PR title as the commit message:
gh api -X PATCH repos/AustralianCancerDataNetwork/my-new-plugin \
  -F allow_merge_commit=false -F allow_rebase_merge=false -F allow_squash_merge=true \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=BLANK
```

Two more to do by hand: a branch ruleset on `main` (one approval, linear history, force pushes and deletion blocked, `label-gate / check` and `build-test / test` as required checks, admin bypass for setup), and a pending PyPI trusted publisher pointing at workflow `publish.yml` in environment `pypi`. The [cava-devops setup guide](https://australiancancerdatanetwork.github.io/cava-devops/guides/setup-new-repo/) walks through both.

## Things that look broken and aren't

Your version will be something like `0.1.dev3+g1a2b3c4`. That's `hatch-vcs` reading the version out of git tags, and a new repo hasn't got any yet. Publishing your first release creates the first tag and the version settles down. Resist the urge to put a static `version =` back into `pyproject.toml`.

`groundworkers` is pinned to a git branch in `[tool.uv.sources]`. The `groundworkers.plugins` entry-point group only exists on the `plugins` branch at the moment; the published 0.4.0 will install your plugin quite happily and then never load it. Treat that pin as a release blocker, because uv sources don't make it into wheel metadata, so anything you publish while it's there would resolve back to the broken 0.4.0. Once groundworkers 0.5.0 ships, drop the pin and move the dependency to `groundworkers>=0.5,<1`.

## Keeping the template useful

The template is an ordinary repo, so improve it with a labelled PR like anything else. Just remember that generated repos have no link back, so a change here only reaches plugins created after it. If you fix something that existing plugins also got wrong, go and fix them too.
