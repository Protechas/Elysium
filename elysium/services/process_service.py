"""Process cleanup for ELYSIUM and child apps."""

from __future__ import annotations

import logging
import os
import time

from elysium.core.paths import get_stop_flow_script_path, resolve_app_dir
from elysium.services.app_registry import AppRegistry
from elysium.windows.powershell import run_ps_file, run_ps_script
from elysium.windows.process_flags import no_window_flags

logger = logging.getLogger("Elysium.ProcessService")


def close_other_elysium_instances(current_pid: int | None = None) -> None:
    import os as _os

    pid = current_pid if current_pid is not None else _os.getpid()
    ps_script = (
        f"$current = {pid}; "
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.ProcessId -ne $current -and ("
        "($_.CommandLine -and ("
        "$_.CommandLine -like '*ELYSIUM.py*' -or "
        "$_.CommandLine -like '*elysium_launcher.py*' -or "
        "$_.CommandLine -like '*ElysiumLauncher.exe*'"
        ")) -or $_.Name -in @('ElysiumLauncher.exe', 'ELYSIUM.exe')"
        ") } | ForEach-Object { "
        "try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} "
        "}"
    )
    try:
        result = run_ps_script(ps_script, timeout=30)
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                if line.strip():
                    logger.info(line.strip())
    except Exception as exc:
        logger.warning("Could not close other ELYSIUM instances: %s", exc)
    time.sleep(0.5)


def stop_flow_server(registry: AppRegistry | None = None) -> None:
    registry = registry or AppRegistry()
    flow = registry.get("flow")
    if not flow:
        return
    flow_dir = resolve_app_dir(flow.id, flow.folder_name())
    if not os.path.isdir(os.path.join(flow_dir, "launcher")):
        return

    stop_script = get_stop_flow_script_path()
    logger.info("Stopping any stale Flow server processes")
    try:
        if stop_script:
            result = run_ps_file(stop_script, ["-FlowDir", flow_dir], timeout=60)
            if result.stdout:
                logger.info(result.stdout.strip())
        else:
            flow_escaped = flow_dir.replace("'", "''")
            ps_script = (
                f"$FlowDir = '{flow_escaped}'; "
                "$PidFile = Join-Path $FlowDir 'launcher\\logs\\server.pid'; "
                "$ServerLog = Join-Path $FlowDir 'launcher\\logs\\server.log'; "
                "$Port = 3000; "
                "if (Test-Path $PidFile) { "
                "$p = Get-Content $PidFile -EA SilentlyContinue; "
                "if ($p) { Stop-Process -Id $p -Force -EA SilentlyContinue }; "
                "Remove-Item $PidFile -Force -EA SilentlyContinue }; "
                "1..4 | ForEach-Object { "
                "$c = Get-NetTCPConnection -LocalPort $Port -State Listen -EA SilentlyContinue | Select -First 1; "
                "if (-not $c) { return }; "
                "Stop-Process -Id $c.OwningProcess -Force -EA SilentlyContinue; "
                "Start-Sleep -Milliseconds 500 }; "
                "if (Test-Path $ServerLog) { Remove-Item $ServerLog -Force -EA SilentlyContinue }"
            )
            run_ps_script(ps_script, timeout=60)
    except Exception as exc:
        logger.warning("Could not stop Flow server: %s", exc)
    time.sleep(0.5)


def patch_flow_launcher(flow_dir: str) -> None:
    ps1_path = os.path.join(flow_dir, "launcher", "launch-flow.ps1")
    if not os.path.isfile(ps1_path):
        return
    try:
        with open(ps1_path, encoding="utf-8") as f:
            content = f.read()
        patch_marker = "Stop-FlowServer\n    if (Test-Path $ServerLog)"
        if patch_marker in content:
            return
        old_block = (
            "function Start-FlowServer {\n"
            "    Ensure-Dependencies\n"
            "\n"
            "    # Dev mode keeps client bundles in sync with source (production start can break clicks)."
        )
        new_block = (
            "function Start-FlowServer {\n"
            "    Stop-FlowServer\n"
            "    if (Test-Path $ServerLog) {\n"
            "        Remove-Item $ServerLog -Force -ErrorAction SilentlyContinue\n"
            "    }\n"
            "    Ensure-Dependencies\n"
            "\n"
            "    # Dev mode keeps client bundles in sync with source (production start can break clicks)."
        )
        if old_block not in content:
            logger.warning("Flow launcher patch skipped: Start-FlowServer block not found")
            return
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write(content.replace(old_block, new_block, 1))
        logger.info("Patched Flow launcher to release server.log before startup")
    except OSError as exc:
        logger.warning("Could not patch Flow launcher: %s", exc)


def close_stale_application_state(current_pid: int | None = None) -> None:
    close_other_elysium_instances(current_pid)
    try:
        registry = AppRegistry()
        stop_flow_server(registry)
        flow = registry.get("flow")
        if flow:
            patch_flow_launcher(resolve_app_dir(flow.id, flow.folder_name()))
    except Exception as exc:
        logger.warning("Deferred startup cleanup failed: %s", exc)
