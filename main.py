import sys
from pathlib import Path
import hashlib
import zipfile

import httpx
from loguru import logger
from pydantic import HttpUrl, ValidationError

from schemas import VPMPackage, VPMPackageIndex, VPMRepository


def check_zip_file(pkg: VPMPackage) -> bool:
    # download zip file
    r = httpx.get(str(pkg.url), follow_redirects=True)
    if r.status_code >= 400:
        logger.error(f"Failed to download {pkg.url}: {r.status_code}")
        return False
    # save as zip file
    zip_path = (
        Path(__file__).resolve().parent / "packages" / f"{pkg.name}-{pkg.version}.zip"
    )
    with zip_path.open("wb") as f:
        f.write(r.content)
    # zip file check
    if not zipfile.is_zipfile(zip_path):
        logger.error(f"Invalid zip file: {zip_path}")
        return False
    # delete zip file
    zip_path.unlink(missing_ok=True)

    # hash check
    sha256sum = hashlib.sha256(r.content).hexdigest()
    if pkg.zipSHA256 is None:
        logger.warning(f"No SHA256 provided for {pkg.url}, filling with {sha256sum}")
        pkg.zipSHA256 = sha256sum
    elif pkg.zipSHA256 != sha256sum:
        logger.error(f"Hash mismatch for {pkg.url}: {pkg.zipSHA256} != {sha256sum}")
        return False
    else:
        logger.debug(f"Hash match for {pkg.url}: {pkg.zipSHA256} == {sha256sum}")

    return True


def read_latest_packages(search_dir: Path) -> list[VPMPackage]:
    latest_packages = []
    for pkg_latest_path in search_dir.glob("*.json"):
        with pkg_latest_path.open("r") as f:
            pkg_latest_json = f.read()
            try:
                pkg_latest = VPMPackage.model_validate_json(pkg_latest_json)
            except ValidationError as e:
                logger.error(f"Error validating {pkg_latest_path}: {str(e)}")
                sys.exit(1)
            logger.debug(
                f"Found package: {pkg_latest.name}@{pkg_latest.version} in {pkg_latest_path}"
            )
            if not check_zip_file(pkg_latest):
                sys.exit(1)
            latest_packages.append(pkg_latest)

    return latest_packages


def generate_vpm_repo(
    pkg_dir: Path,
    author: str = "VirtualAviationJapan",
    name: str = "VirtualAviationJapan",
    id: str = "jp.virtualaviation",
    url: HttpUrl = HttpUrl("https://virtualaviationjapan.github.io/vpm/vpm.json"),
) -> VPMRepository:
    vpm = VPMRepository(author=author, name=name, id=id, url=url, packages={})
    latest_packages = read_latest_packages(pkg_dir)
    for pkg in latest_packages:
        if pkg.name not in vpm.packages:
            logger.debug(f"Adding new package {pkg.name} to VPM repository")
            vpm.packages[pkg.name] = VPMPackageIndex(versions={pkg.version: pkg})
        else:
            vpm.packages[pkg.name].add_version(pkg)
    return vpm


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: uv run main.py <output>")
        logger.error("output are relative to the project directory")
        sys.exit(1)
    project_dir = Path(__file__).resolve().parent

    vpm_repo = generate_vpm_repo(project_dir / "packages")
    logger.debug(vpm_repo.model_dump_json(indent=2))
    output_path = (project_dir / sys.argv[1]).resolve()
    with open(output_path, "w") as f:
        f.write(vpm_repo.model_dump_json(indent=2))
    logger.info(f"Updated VPM repository is {output_path}")
