#!/usr/bin/env python3
"""Build a Debian package for blackcell-watchdog without external tooling."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import re
import shutil
import tarfile
import textwrap
import time

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    tomllib = None  # type: ignore[assignment]

PACKAGE_NAME = "blackcell-watchdog"
BINARIES = ["watchdog", "watchdog-tui"]


def read_version(pyproject: Path) -> str:
    data = pyproject.read_text(encoding="utf-8")
    if tomllib is not None:
        parsed = tomllib.loads(data)
        return parsed["project"]["version"]
    match = re.search(r'version\s*=\s*"([^"]+)"', data)
    if not match:
        raise RuntimeError("Unable to determine version from pyproject.toml.")
    return match.group(1)


def copy_package(src_dir: Path, dst_dir: Path) -> None:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(src_dir, dst_dir)


def write_file(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    os.chmod(path, mode)


def create_entrypoint(path: Path, module: str) -> None:
    script = textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        exec python3 -m {module} "$@"
        """
    )
    write_file(path, script, mode=0o755)


def create_dist_info(dist_dir: Path, version: str) -> None:
    metadata = textwrap.dedent(
        f"""\
        Metadata-Version: 2.1
        Name: watchdog-cli
        Version: {version}
        Summary: Shell session logger with SQLite index and Textual TUI
        """
    )
    write_file(dist_dir / "METADATA", metadata)
    write_file(dist_dir / "INSTALLER", "pip\n")
    wheel = textwrap.dedent(
        """\
        Wheel-Version: 1.0
        Generator: build_deb.py
        Root-Is-Purelib: true
        Tag: py3-none-any
        """
    )
    write_file(dist_dir / "WHEEL", wheel)
    write_file(dist_dir / "RECORD", "")


def build_tar(source: Path, tar_path: Path, arcname: str | None = None) -> None:
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as tar:
        if arcname:
            tar.add(source, arcname=arcname)
        else:
            for item in sorted(source.iterdir()):
                tar.add(item, arcname=item.name)


def build_debian_binary(path: Path) -> None:
    write_file(path, "2.0\n")


@dataclass
class ArMember:
    name: str
    path: Path
    mode: int = 0o100644


def build_ar(archive: Path, members: list[ArMember]) -> None:
    if archive.exists():
        archive.unlink()
    with archive.open("wb") as ar:
        ar.write(b"!<arch>\n")
        for member in members:
            data = member.path.read_bytes()
            stat = member.path.stat()
            header = [
                (member.name + "/").encode("ascii").ljust(16, b" "),
                f"{int(stat.st_mtime)}".rjust(12).encode("ascii"),
                b"0".rjust(6),
                b"0".rjust(6),
                f"{member.mode:o}".rjust(8).encode("ascii"),
                f"{len(data)}".rjust(10).encode("ascii"),
                b"`\n",
            ]
            ar.write(b"".join(header))
            ar.write(data)
            if len(data) % 2 == 1:
                ar.write(b"\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Debian package for blackcell-watchdog.")
    parser.add_argument(
        "--output",
        default="dist/deb",
        help="Output directory for the .deb (default: dist/deb)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    pyproject = repo_root / "pyproject.toml"
    version = read_version(pyproject)
    staging_root = Path(args.output).resolve()
    staging_dir = staging_root / f"{PACKAGE_NAME}_{version}"
    debian_dir = staging_dir / "DEBIAN"
    usr_bin = staging_dir / "usr" / "bin"
    pkg_lib = staging_dir / "usr" / "lib" / "python3" / "dist-packages"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    debian_dir.mkdir(parents=True, exist_ok=True)
    usr_bin.mkdir(parents=True, exist_ok=True)
    pkg_lib.mkdir(parents=True, exist_ok=True)

    copy_package(repo_root / "src" / "watchdog", pkg_lib / "watchdog")
    create_dist_info(pkg_lib / f"watchdog_cli-{version}.dist-info", version)
    create_entrypoint(usr_bin / "watchdog", "watchdog.cli")
    create_entrypoint(usr_bin / "watchdog-tui", "watchdog.tui.app")

    control = textwrap.dedent(
        f"""\
        Package: {PACKAGE_NAME}
        Version: {version}
        Section: utils
        Priority: optional
        Architecture: all
        Depends: python3, python3-textual
        Maintainer: Watchdog <watchdog@example.com>
        Description: Watchdog shell session logger with SQLite and Textual TUI
         A per-user shell history/logging tool from the Blackcell project.
        """
    )
    write_file(debian_dir / "control", control)
    postinst = textwrap.dedent(
        """\
        #!/bin/sh
        set -e
        echo "blackcell-watchdog installed."
        echo "Run 'watchdog install' as your normal user to enable shell logging."
        exit 0
        """
    )
    write_file(debian_dir / "postinst", postinst, mode=0o755)

    control_tar = staging_root / "control.tar.gz"
    data_tar = staging_root / "data.tar.gz"
    debian_binary = staging_root / "debian-binary"

    build_tar(debian_dir, control_tar)
    build_tar(staging_dir / "usr", data_tar, "usr")
    build_debian_binary(debian_binary)

    deb_path = staging_root / f"{PACKAGE_NAME}_{version}_all.deb"
    build_ar(
        deb_path,
        [
            ArMember("debian-binary", debian_binary),
            ArMember("control.tar.gz", control_tar),
            ArMember("data.tar.gz", data_tar),
        ],
    )

    control_tar.unlink(missing_ok=True)
    data_tar.unlink(missing_ok=True)
    debian_binary.unlink(missing_ok=True)

    print(f"Debian package created at: {deb_path}")
    print("Staged filesystem remains under:", staging_dir)


if __name__ == "__main__":
    main()
