import sys
from pathlib import Path

from pydantic import ValidationError

from schemas import VPMPackage, VPMPackageIndex, VPMRepository


def read_latest_packages(search_dir: Path) -> list[VPMPackage]:
    latest_packages = []
    for pkg_latest_path in (search_dir).glob("*.json"):
        with pkg_latest_path.open("r") as f:
            pkg_latest_json = f.read()
            try:
                pkg_latest = VPMPackage.model_validate_json(pkg_latest_json)
            except ValidationError as e:
                print(sys.stderr, f"Error validating {pkg_latest_path.name}: {str(e)}")
                sys.exit(1)
            else:
                print(
                    f"INFO: Found package: {pkg_latest.name}@{pkg_latest.version} in {pkg_latest_path}"
                )
                latest_packages.append(pkg_latest)

    return latest_packages


def update_vpm_repo(vpm_path: Path, pkg_dir: Path) -> bool:
    with open(vpm_path, "r") as f:
        vpm_data = f.read()
        try:
            vpm = VPMRepository.model_validate_json(vpm_data)
        except ValidationError as e:
            print(sys.stderr, f"Error validating vpm.json: {str(e)}")
            sys.exit(1)
        latest_packages = read_latest_packages(pkg_dir)
        for pkg in latest_packages:
            if pkg.name not in vpm.packages:
                print(f"INFO: Adding new package {pkg.name} to VPM repository")
                vpm.packages[pkg.name] = VPMPackageIndex(versions={pkg.version: pkg})
            else:
                vpm.packages[pkg.name].add_version(pkg)
    with open(vpm_path, "w") as f:
        f.write(vpm.model_dump_json(indent=2))
    return True


if __name__ == "__main__":
    project_dir = Path(__file__).resolve().parent

    update_vpm_repo(project_dir / "vpm.json", project_dir / "packages")
    print("INFO: VPM repository updated successfully")
