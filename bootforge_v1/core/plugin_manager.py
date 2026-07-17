from __future__ import annotations

import importlib.util
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterable

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    entry: str
    enabled: bool = True


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    module: ModuleType


class PluginManager:
    """Loads only plugins that declare a valid local manifest.json."""

    def __init__(self, plugins_dir: Path) -> None:
        self.plugins_dir = plugins_dir.resolve()

    def discover(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        if not self.plugins_dir.exists():
            return manifests

        for manifest_path in sorted(self.plugins_dir.glob("*/manifest.json")):
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest = PluginManifest(
                    plugin_id=str(data["id"]),
                    name=str(data["name"]),
                    version=str(data["version"]),
                    entry=str(data.get("entry", "plugin.py")),
                    enabled=bool(data.get("enabled", True)),
                )
                entry_path = (manifest_path.parent / manifest.entry).resolve()
                entry_path.relative_to(self.plugins_dir)
                if not entry_path.is_file():
                    raise FileNotFoundError(entry_path)
                manifests.append(manifest)
            except (KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
                LOGGER.error("Rejected plugin manifest %s: %s", manifest_path, exc)
        return manifests

    def load(self, manifest: PluginManifest) -> LoadedPlugin:
        if not manifest.enabled:
            raise RuntimeError(f"Plugin {manifest.plugin_id} is disabled")

        entry_path = (self.plugins_dir / manifest.plugin_id / manifest.entry).resolve()
        entry_path.relative_to(self.plugins_dir)
        spec = importlib.util.spec_from_file_location(
            f"bootforge_plugin_{manifest.plugin_id}", entry_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to create import spec for {entry_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not callable(getattr(module, "get_tool_widget", None)):
            raise TypeError(f"Plugin {manifest.plugin_id} lacks get_tool_widget()")
        return LoadedPlugin(manifest=manifest, module=module)

    def load_all(self, manifests: Iterable[PluginManifest]) -> list[LoadedPlugin]:
        loaded: list[LoadedPlugin] = []
        for manifest in manifests:
            try:
                loaded.append(self.load(manifest))
            except Exception:
                LOGGER.exception("Plugin %s failed to load", manifest.plugin_id)
        return loaded
