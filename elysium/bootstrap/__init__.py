"""Startup bootstrap helpers (stdlib-only; safe before third-party imports)."""

from elysium.bootstrap.repo_sync import ensure_runtime_ready

__all__ = ["ensure_runtime_ready"]
