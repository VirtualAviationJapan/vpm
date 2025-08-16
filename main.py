import sys
from pathlib import Path

from pydantic import ValidationError

from schemas import VPMPackage


def read_latest_packages() -> dict[str, VPMPackage]:
    project_dir = Path(__file__).resolve().parent
    latest_packages = {}
    for pkg_latest_path in (project_dir / "packages").glob("*.json"):
        with pkg_latest_path.open("r") as f:
            pkg_latest_json = f.read()
            try:
                pkg_latest = VPMPackage.model_validate_json(pkg_latest_json)
            except ValidationError as e:
                print(sys.stderr, f"Error validating {pkg_latest_path.name}: {str(e)}")
                sys.exit(1)
            else:
                print(f"Found package: {pkg_latest.name} version {pkg_latest.version}")
                latest_packages[pkg_latest.name] = pkg_latest

    return latest_packages


if __name__ == "__main__":
    packages = read_latest_packages()
    print(packages)
