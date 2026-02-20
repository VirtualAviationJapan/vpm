import json
import re
import sys
from pathlib import Path
from typing import Optional

from github import Github
from loguru import logger
from pydantic import HttpUrl, ValidationError

from schemas import VPMPackage, VPMPackageIndex, VPMRepository


def get_zip_hash_from_github(url: HttpUrl) -> Optional[str]:
    m = re.match(
        r"^https?://github\.com/(.*)/(.*)/releases/download/(.*)/.*$", str(url)
    )
    if m is None:
        logger.warning(f"{url} is not a GitHub release!")
        return None

    repo_owner, repo_name, release_tag = m.groups()
    g = Github()
    repo = g.get_repo(f"{repo_owner}/{repo_name}")
    release = repo.get_release(release_tag)
    asset_hash: Optional[str] = {
        HttpUrl(asset.browser_download_url): asset.digest for asset in release.assets
    }[url]
    logger.debug(f"GitHub release asset {url} has hash {asset_hash}")
    if asset_hash is None:
        return None
    else:
        hash_ret: str = asset_hash.removeprefix("sha256:")
        if hash_ret.startswith("sha256:"):
            logger.warning(f"Unexpected hash format: {asset_hash}")
            return None
        else:
            return hash_ret.removeprefix("sha256:")


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
            if pkg_latest.zipSHA256 is None:
                hash = get_zip_hash_from_github(pkg_latest.url)
                if hash is None:
                    logger.warning(
                        f"zipSHA256 is empty in {pkg_latest.name}@{pkg_latest.version}"
                    )
                else:
                    logger.info(
                        f"zipSHA256 is appended into {pkg_latest.name}@{pkg_latest.version}"
                    )
            latest_packages.append(pkg_latest)

    return latest_packages


def generate_vpm_repo(
    pkg_dir: Path,
    author: str,
    id: str,
    name: str,
    url: HttpUrl,
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
    if len(sys.argv) < 6:
        logger.error("Usage: uv run main.py <author> <id> <name> <url> <output>")
        logger.error("output are relative to the project directory")
        sys.exit(1)
    project_dir = Path(__file__).resolve().parent
    (author, id, name, url, out_path) = (
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
        HttpUrl(sys.argv[4]),
        sys.argv[5],
    )

    vpm_repo = generate_vpm_repo(project_dir / "packages", author, id, name, url)
    logger.debug(vpm_repo.model_dump_json(indent=2))

    output_path = (project_dir / out_path).resolve()
    with open(output_path, "w") as f:
        json.dump(
            vpm_repo.model_dump(mode="json", exclude_none=True),
            f,
            indent=2,
            sort_keys=True,
        )
    logger.info(f"Updated VPM repository is {output_path}")
