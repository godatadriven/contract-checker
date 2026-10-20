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
   [semantic versioning](https://semver.org/), targeting `main`. For a release candidate use
   `vX.Y.ZrcN` (e.g. `v0.2.0rc1`) and tick **Set as a pre-release**.
1. Write the release notes and click **Publish release**.

!!! warning "Use the PEP 440 tag form"
    Write release candidates as `v0.1.0rc1`, not `v0.1.0-rc1`. The workflow checks that the built
    version equals the tag (minus the leading `v`) and fails before publishing if they differ.

Publishing the release triggers the
[`Release` workflow](https://github.com/godatadriven/contract-checker/blob/main/.github/workflows/release.yml),
which:

1. Checks out the tagged commit (with full history, so `setuptools-scm` can resolve the version).
1. Runs the test suite against the tagged commit — PyPI uploads are immutable, so a release that
   fails its tests never reaches PyPI.
1. Builds the sdist and wheel with `uv build` and checks their version matches the tag.
1. Publishes them to PyPI via
   [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API tokens stored
   in the repo).

Once the workflow finishes, the new version is available:

```shell
uvx contract-checker --version   # or: pipx install contract-checker
```

Pre-releases are not installed by default. Request one explicitly:

```shell
uvx contract-checker@0.1.0rc1 --version   # or: pip install --pre contract-checker
```
