# Distribution and Release Guide

WorkForge is a public Python CLI distributed through PyPI. GitHub remains the
source repository and release record. Users can run WorkForge in an isolated
environment without cloning the repository or creating a development setup.

## Current state

The release workflow tests and builds WorkForge, updates the version and
changelog, creates a Git tag, and uploads the wheel and source distribution to
both a GitHub Release and PyPI. The PyPI job uses Trusted Publishing and a
separate GitHub environment so it never receives the repository write token.

## Choose how to run WorkForge

`uvx` ships with `uv`; users who do not have it can follow the
[official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### On demand in a project

Use `uvx` when WorkForge supports planning for a project but should not become a
permanent command or project dependency:

```bash
cd my-project
uvx workforge init .workforge \
  --name my-project \
  --provider github \
  --namespace organization/repository
uvx workforge preview .workforge/inbox/requirements.md --workspace .workforge
```

Prefix every command with `uvx`. The WorkForge runtime remains isolated and uv
may cache it for faster later executions; the project-local `.workforge`
workspace persists normally. The same approach works with Trello, GitHub
Projects, and Jira.

To reproduce planning behavior with a known release, pin it in each invocation:

```bash
uvx workforge@X.Y.Z preview .workforge/inbox/requirements.md --workspace .workforge
```

There is nothing to uninstall after `uvx`. `uv cache clean` removes uv's shared
cache, not only WorkForge, and is normally unnecessary.

### Persistent command

Install WorkForge persistently when it is used across many projects or by
scripts that expect a `workforge` command on `PATH`:

```bash
uv tool install workforge
workforge --help
```

Upgrade or remove this installation with:

```bash
uv tool upgrade workforge
uv tool uninstall workforge
```

`pipx` provides an equivalent isolated installation:

```bash
pipx install workforge
```

Plain `pip install workforge` is supported but is not the recommended default
because it can mix WorkForge dependencies with another Python environment.

Pin a persistent installation when reproducibility matters:

```bash
uv tool install workforge==X.Y.Z
```

## First use

Create a workspace inside the project that WorkForge will manage:

```bash
uvx workforge init .workforge \
  --name my-project \
  --provider github \
  --namespace organization/repository
```

The generated `.workforge/README.md` explains how to create provider items from
a Markdown requirement or discover and continue existing items using `uvx`.

Keep credentials and generated output out of version control:

```gitignore
.workforge/.env
.workforge/output/
```

Copy `.workforge/.env.example` to `.workforge/.env`, add the selected provider's
credentials, and validate them before performing writes:

```bash
uvx workforge providers test --workspace .workforge --provider github
```

Place Markdown requirements in `.workforge/inbox/`. Preview them first:

```bash
uvx workforge preview .workforge/inbox/requirements.md --workspace .workforge
```

Create external planning items only after reviewing the preview:

```bash
uvx workforge create .workforge/inbox/requirements.md \
  --workspace .workforge \
  --provider github \
  --execute \
  --save
```

Provider setup and the remaining commands are documented in the main README and
provider design documents.

## One-time PyPI setup

Before the first public release, a project owner must:

1. Create and verify a PyPI account with two-factor authentication enabled.
2. Confirm that the `workforge` project name is available and create the PyPI
   project through its first publish or PyPI's pending-publisher flow.
3. Configure a PyPI Trusted Publisher for GitHub repository
   `Nanielito/workforge`, workflow `release.yml`, and the GitHub environment
   selected for publishing (recommended: `pypi`).
4. Create the matching protected GitHub environment and require approval if a
   second pair of eyes is desired for production publication.
5. Confirm the publish job has only `id-token: write`; do not store a long-lived
   PyPI API token in the repository.

The release workflow publishes with the official
`pypa/gh-action-pypi-publish` action after the distributions pass tests, build,
and metadata validation. Keep third-party GitHub Actions on reviewed versions
and their permissions minimal.

TestPyPI may be used for an initial pipeline check, but it has a separate account,
project namespace, and package index. Passing TestPyPI does not reserve the name
on production PyPI.

## Maintainer release process

### Before release

1. Ensure the intended changes are merged into `main` and the working tree is
   represented by CI.
2. Confirm CI passes for every supported Python version and the package build.
3. Review user-visible changes and select the SemVer bump:
   `patch` for compatible fixes, `minor` for compatible features, or `major` for
   breaking interfaces.
4. Confirm the target version does not already exist as a Git tag, GitHub
   Release, or PyPI release.

Do not edit the version or generated changelog manually. The release workflow
owns both.

### Release

From GitHub Actions, run the `Release` workflow on `main` and choose the bump.
The target workflow is:

1. Run the test suite.
2. Calculate and write the new version.
3. Generate `CHANGELOG.md`.
4. Build the wheel and source distribution once.
5. Validate both artifacts with `twine check`.
6. Commit the release metadata, create the tag, and push them.
7. Create the GitHub Release with the built artifacts.
8. Publish those exact artifacts to PyPI through Trusted Publishing.

Building once matters: GitHub and PyPI should expose identical artifacts for a
given version.

### Verify the release

After the workflow succeeds:

1. Confirm the version appears on PyPI and the GitHub Release.
2. Install into a clean isolated environment:

   ```bash
   uvx workforge@X.Y.Z --help
   ```

3. Check the reported version or package metadata and run a safe local command
   such as `workforge preview` against an example workspace.
4. Confirm no credentials, `.env` files, generated workspace output, or other
   unintended files are present in the source distribution.

## Failed releases and corrections

PyPI release files are immutable. Never rebuild different contents under an
existing version. If a published release is wrong, fix the source and publish a
new patch version.

If a version is unsafe or unusable, yank it on PyPI and explain why in the
release notes. Yanking discourages new installations while preserving builds
that explicitly pin the version. Deleting a release is a last resort and does
not make its version reusable.

If GitHub publication succeeds but PyPI publication fails, do not rerun the
entire version-bump workflow. Diagnose the publish job and retry publication of
the already-built, validated artifacts. The final workflow design should keep
the build artifacts available for that retry.

## Security and compatibility

- Publishing to PyPI makes the packaged Python source publicly downloadable.
- Workspace credentials remain local and must never enter distributions,
  fixtures, logs, or release artifacts.
- Release jobs should use Trusted Publishing, short-lived OIDC credentials, and
  minimal GitHub permissions.
- CLI commands, options, configuration, JSON fields, and saved output are public
  interfaces governed by SemVer.
- Keep Python compatibility aligned with `requires-python` and the CI matrix.
- Consumers that require deterministic behavior should pin an exact WorkForge
  version and upgrade deliberately.

Homebrew formulas, Docker images, and standalone binaries are intentionally out
of scope. Add another channel only when users need installation without a Python
tool runner or when operational usage requires a container image.
