from __future__ import annotations

import hashlib
import os
import tempfile
import threading
from pathlib import Path
from typing import ClassVar

from services.core.settings import Settings
from services.core.tools.base import ToolResult

IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "data",
    "mad_assistant.egg-info",
}

ALLOWED_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}


class WorkspaceListTool:
    name = "workspace.list"
    description = "Lista archivos del proyecto MAD ignorando caches y datos locales."

    def __init__(self, settings: Settings) -> None:
        self.root = settings.workspace_root.resolve()

    async def run(self, arguments: dict) -> ToolResult:
        limit = int(arguments.get("limit", 80))
        files = []
        for path in self.root.rglob("*"):
            if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
                continue
            files.append(str(path.relative_to(self.root)).replace("\\", "/"))
            if len(files) >= limit:
                break
        return ToolResult(text="Archivos: " + ", ".join(files), data={"files": files})


class WorkspaceCreateFileTool:
    name = "workspace.create_file"
    description = "Crea, anade o reemplaza contenido con lectura de verificacion dentro del workspace."
    parameters: ClassVar[dict] = {
        "path": {"type": "string"}, "content": {"type": "string"},
        "mode": {"type": "string", "enum": ["create", "append", "replace"]},
        "expected_sha256": {"type": "string"}, "overwrite_existing": {"type": "boolean"},
        "confirm": {"type": "boolean"}, "confirmation_id": {"type": "string"},
    }
    _lock = threading.RLock()

    def __init__(self, settings: Settings) -> None:
        self.root = settings.workspace_root.resolve()

    def preflight(self, arguments: dict) -> dict:
        try:
            exists = self._safe_target(str(arguments.get("path", ""))).exists()
        except ValueError:
            exists = False
        return {**arguments, "overwrite_existing": exists and arguments.get("mode") == "replace"}

    async def run(self, arguments: dict) -> ToolResult:
        with self._lock:
            return self._write(arguments)

    def _write(self, arguments: dict) -> ToolResult:
        relative_path = str(arguments.get("path", "")).strip()
        content = str(arguments.get("content", ""))
        try:
            target = self._safe_target(relative_path)
            mode = str(arguments.get("mode", "create"))
            if mode not in {"create", "append", "replace"}:
                raise ValueError("Modo de escritura no valido")
            if len(content.encode("utf-8")) > 128_000:
                raise ValueError("El contenido supera el limite de 128 KB")
            exists = target.exists()
            before = target.read_bytes() if exists else b""
            if len(before) > 128_000:
                raise ValueError("El archivo supera el limite de 128 KB")
            if exists and mode == "create":
                raise ValueError("El archivo ya existe. No lo he sobrescrito; indica si quieres anadir o reemplazar.")
            if mode == "append" and not exists:
                raise ValueError("No existe el archivo que quieres actualizar")
            if mode == "replace" and not exists:
                raise ValueError("No existe el archivo que quieres reemplazar; usa crear")
            if mode == "replace" and exists and arguments.get("confirm") is not True:
                raise ValueError("Reemplazar contenido existente requiere confirmacion concreta")
            if exists and mode in {"append", "replace"} and arguments.get("expected_sha256") != hashlib.sha256(before).hexdigest():
                raise ValueError("El archivo cambio o falta su hash de lectura. Vuelve a leerlo antes de escribir.")
            encoded = content.encode("utf-8")
            if mode == "append":
                if not content.strip():
                    raise ValueError("Falta el contenido que quieres anadir")
                if content.strip() in before.decode("utf-8").splitlines():
                    return ToolResult("Ese contenido ya esta en el archivo; no lo he duplicado.", {
                        "confirmed": True, "changed": False, "path": str(target),
                        "sha256": hashlib.sha256(before).hexdigest(), "verified_by": "read_existing_content",
                    })
                encoded = (b"" if before.endswith(b"\n") else b"\n") + encoded + (b"" if encoded.endswith(b"\n") else b"\n")
            expected = before + encoded if mode == "append" else encoded
            if len(expected) > 128_000:
                raise ValueError("La nota resultante supera el limite de 128 KB")
            target.parent.mkdir(parents=True, exist_ok=True)
            if mode == "replace":
                with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(encoded)
                try:
                    if target.read_bytes() != before:
                        raise ValueError("El archivo cambio antes de reemplazarlo. No he aplicado el reemplazo.")
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
            else:
                with target.open("ab" if mode == "append" else "xb") as stream:
                    stream.write(encoded)
            observed = target.read_bytes()
            confirmed = observed == expected
            return ToolResult(
                f"Archivo {'actualizado' if exists else 'creado'} y verificado: {relative_path}"
                if confirmed else "He escrito el archivo, pero su lectura final no coincide. Revisa el contenido.",
                {"created": not exists, "changed": True, "confirmed": confirmed,
                 "path": str(target), "sha256": hashlib.sha256(observed).hexdigest(),
                 "verified_by": "read_after_write", "bytes": len(observed)},
            )
        except (OSError, UnicodeError, ValueError) as exc:
            return ToolResult(f"No he completado la escritura: {exc}", {
                "created": False, "confirmed": False, "executed": False, "error": str(exc),
            })

    def _safe_target(self, relative_path: str) -> Path:
        # Reject Windows drive paths and alternate data streams on every OS,
        # including Linux where Path("C:/x") would otherwise be relative.
        if (
            not relative_path
            or "\\" in relative_path
            or ":" in relative_path
            or Path(relative_path).is_absolute()
            or Path(relative_path).drive
        ):
            raise ValueError("Necesito una ruta relativa dentro del workspace permitido")
        target = (self.root / relative_path).resolve()
        if self.root != target and self.root not in target.parents:
            raise ValueError("Path fuera del workspace permitido")
        if any(part in IGNORED_PARTS or part.startswith(".") for part in target.relative_to(self.root).parts):
            raise ValueError("Ruta interna o privada no permitida")
        if target.suffix not in ALLOWED_SUFFIXES:
            raise ValueError(f"Extension no permitida: {target.suffix}")
        return target


class WorkspaceReadFileTool(WorkspaceCreateFileTool):
    name = "workspace.read_file"
    description = "Lee un archivo de texto autorizado y devuelve contenido y SHA256."
    parameters: ClassVar[dict] = {"path": {"type": "string"}}

    async def run(self, arguments: dict) -> ToolResult:
        try:
            target = self._safe_target(str(arguments.get("path", "")))
            if target.stat().st_size > 128_000:
                raise ValueError("El archivo supera el limite de 128 KB")
            content = target.read_bytes()
            return ToolResult(content.decode("utf-8"), {
                "content": content.decode("utf-8"), "path": str(target),
                "sha256": hashlib.sha256(content).hexdigest(), "grounded": True,
            })
        except (OSError, UnicodeError, ValueError) as exc:
            return ToolResult(f"No pude leer el archivo: {exc}", {"error": str(exc), "available": False})
