from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "manifest",
    [Path("vendor/SHA256SUMS"), Path("fixtures/catalog/SHA256SUMS")],
)
def test_committed_artifacts_match_recorded_sha256(manifest: Path) -> None:
    for line in manifest.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split(maxsplit=1)
        artifact = manifest.parent / filename
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == expected
