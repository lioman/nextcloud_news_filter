from pdm.backend.hooks.version import SCMVersion


def format_version(version: SCMVersion) -> str:
    appendix = f".dev{version.distance}" if version.distance else ""
    return f"{version.version}{appendix}"
