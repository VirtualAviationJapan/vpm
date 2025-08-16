from typing import Dict, Optional
from pydantic import BaseModel, HttpUrl, ConfigDict


class Author(BaseModel):
    name: str
    email: str


class VPMPackage(BaseModel):
    """
    Data model representing a VPM package configuration.

    Attributes:
        name (str): Unique identifier of the package.
        displayName (str): Human-readable name for display purposes.
        version (str): The version string of the package.
        url (HttpUrl): URL pointing to the direct download location of the package.
        author (Author): Information about the package author.

        description (Optional[str]): A brief summary or description of the package.
        unity (Optional[str]): The Unity version compatible with the package.
        documentationUrl (Optional[HttpUrl]): URL of the package documentation.
        changelogUrl (Optional[HttpUrl]): URL for the package changelog.
        vpmDependencies (Dict[str, str]): Dependencies defined for the package, mapping package names to version constraints.
        zipSHA256 (Optional[str]): SHA256 hash of the package's zip archive.
        license (Optional[str]): License information for the package.
        
    Note:
        Format is written on https://vcc.docs.vrchat.com/vpm/packages/#package-format
    """
    model_config = ConfigDict(extra="allow")  # allow extra fields
    # required fields for VPM
    name: str
    displayName: str
    version: str
    url: HttpUrl
    author: Author
    # recommended fields from Unity
    description: Optional[str] = None
    unity: Optional[str] = None
    # optional fields from Unity (VPMでは基本的にdependenciesを使わない?)
    documentationUrl: Optional[HttpUrl] = None
    # recommended fields from VPM
    changelogUrl: Optional[HttpUrl] = None
    vpmDependencies: Dict[str, str] = {}
    zipSHA256: Optional[str] = None
    license: Optional[str] = None


class VPMPackageIndex(BaseModel):
    versions: Dict[str, VPMPackage]  # key: version

class VPMRepository(BaseModel):
    """

    """
    author: str
    name: str
    id: str
    url: HttpUrl
    packages: Dict[str, VPMPackageIndex]  # key: package name
