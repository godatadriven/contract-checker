"""Glob-based include/exclude filtering for contract file paths."""

import re
from pathlib import Path
from typing import List


def glob_to_regex(pattern: str) -> re.Pattern:
    """Translate a glob pattern into an anchored, compiled regex.

    Rules:
        - Patterns match the POSIX-style path relative to the contracts base dir.
        - A leading '/' is stripped ('/domain/**' == 'domain/**').
        - '*'  matches within a single path segment (never crosses '/').
        - '**' matches across path segments; '**/' means zero or more directories.
        - '?'  matches one character (not '/'); '[abc]' matches a character set.
        - A pattern with no wildcards is a literal path and matches only itself.

    Args:
        pattern: The glob pattern to translate.

    Returns:
        A compiled regex, anchored at both ends.

    Raises:
        ValueError: If the pattern is empty or ends with a bare '/'.
    """
    pat = pattern.strip().lstrip("/")
    if not pat:
        raise ValueError(f"Empty path pattern: {pattern!r}")
    if pat.endswith("/"):
        raise ValueError(
            f"Invalid path pattern {pattern!r}: directory patterns must end with '/**' (did you mean '{pat}**'?)"
        )

    parts: List[str] = []
    i, n = 0, len(pat)
    while i < n:
        if pat.startswith("**/", i):
            parts.append("(?:.*/)?")  # zero or more whole directories
            i += 3
        elif pat.startswith("**", i):
            parts.append(".*")  # anything, including '/'
            i += 2
        elif pat[i] == "*":
            parts.append("[^/]*")  # anything within one segment
            i += 1
        elif pat[i] == "?":
            parts.append("[^/]")
            i += 1
        elif pat[i] == "[":
            closing = pat.find("]", i + 1)
            if closing == -1:
                parts.append(re.escape(pat[i]))
                i += 1
            else:
                parts.append(pat[i : closing + 1])
                i = closing + 1
        else:
            parts.append(re.escape(pat[i]))
            i += 1

    return re.compile("^" + "".join(parts) + "$")


def filter_contract_paths(
    contract_paths: List[Path],
    base_path: Path,
    include_paths: List[str],
    exclude_paths: List[str],
) -> List[Path]:
    """Apply include/exclude glob filters to discovered contract paths.

    Args:
        contract_paths: Discovered contract file paths (under base_path).
        base_path: Directory the patterns are relative to.
        include_paths: Glob patterns to include. Empty list includes everything.
        exclude_paths: Glob patterns to exclude. Applied after includes and wins.

    Returns:
        The paths that are included and not excluded, in input order.
    """
    include_regexes = [glob_to_regex(p) for p in include_paths]
    exclude_regexes = [glob_to_regex(p) for p in exclude_paths]

    filtered = []
    for path in contract_paths:
        relative = path.relative_to(base_path).as_posix()
        included = not include_regexes or any(r.match(relative) for r in include_regexes)
        excluded = any(r.match(relative) for r in exclude_regexes)
        if included and not excluded:
            filtered.append(path)
    return filtered
