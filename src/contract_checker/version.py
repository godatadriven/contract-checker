from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version


def version() -> str:
    """Get the version of `contract-checker`.

    The version is resolved from the installed package metadata, which is
    derived from the latest git tag by `setuptools-scm` at build time.

    Returns:
        str: The version of `contract-checker`.

    """
    try:
        return _package_version("contract_checker")
    except PackageNotFoundError:  # Not installed (e.g. running from a raw checkout).
        return "0.0.0"
