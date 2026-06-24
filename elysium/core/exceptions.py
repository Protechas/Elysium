"""Friendly launcher exceptions."""

from __future__ import annotations


class ElysiumError(Exception):
    """Base error with user-facing and technical messages."""

    friendly_message: str
    recommended_action: str

    def __init__(
        self,
        technical_message: str,
        *,
        friendly_message: str | None = None,
        recommended_action: str | None = None,
    ):
        super().__init__(technical_message)
        self.technical_message = technical_message
        self.friendly_message = friendly_message or technical_message
        self.recommended_action = recommended_action or "View the logs or export diagnostics for support."


class PythonEnvironmentError(ElysiumError):
    pass


class DependencyInstallError(ElysiumError):
    pass


class GitUpdateError(ElysiumError):
    pass


class DownloadError(ElysiumError):
    pass


class LaunchFileMissingError(ElysiumError):
    pass


class PermissionError(ElysiumError):  # noqa: A001
    pass


class NodeMissingError(ElysiumError):
    def __init__(self, technical_message: str = "node.exe was not found"):
        super().__init__(
            technical_message,
            friendly_message="Flow needs Node.js before it can launch.",
            recommended_action="Install Node.js from https://nodejs.org and try again.",
        )
