# Releasing

`contract-checker` is published to [PyPI](https://pypi.org/project/contract-checker/). Releases
are fully automated: publishing a GitHub Release builds the package and uploads it to PyPI.

This page is for **maintainers**. Contributors don't need to do anything here — your changes ship
with the next release.

## How versioning works

The package version is **derived from git tags** by
[`setuptools-scm`](https://setuptools-scm.readthedocs.io/). There is no version string to bump by
hand: the latest `vX.Y.Z` tag *is* the version. The CLI reports it at runtime from the installed
package metadata:

```shell
contract-checker --version
```

## Cutting a release

1. Make sure `main` is green and contains everything you want to ship.
1. On GitHub, go to **Releases → Draft a new release**.
1. Create a new tag of the form `vX.Y.Z` (e.g. `v0.2.0`), following
   [semantic versioning](https://semver.org/), targeting `main`.
1. Write the release notes and click **Publish release**.

Publishing the release triggers the
[`Release` workflow](https://github.com/godatadriven/contract-checker/blob/main/.github/workflows/release.yml),
which:

1. Checks out the tagged commit (with full history, so `setuptools-scm` can resolve the version).
1. Runs the test suite against the tagged commit — PyPI uploads are immutable, so a release that
   fails its tests never reaches PyPI.
1. Builds the sdist and wheel with `uv build`.
1. Publishes them to PyPI via
   [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API tokens stored
   in the repo).

Once the workflow finishes, the new version is available:

```shell
uvx contract-checker --version   # or: pipx install contract-checker
```

!!! tip "Dry-run with a pre-release"
    To exercise the full pipeline without burning a real version number, cut a pre-release tag
    such as `v0.2.0rc1` first. PyPI rejects re-uploads of an already-published version, so a
    release candidate is a safe way to validate the flow.

## One-time setup (already configured)

These steps only need to be done once per project and are recorded here for reference:

- **PyPI Trusted Publisher** — configured on PyPI for owner `godatadriven`, repository
  `contract-checker`, workflow `release.yml`, and environment `pypi`.
- **GitHub `pypi` environment** — defined under **Settings → Environments**; optionally protected
  with required reviewers to add a manual approval gate before the publish step runs.
