# Maddy | Python Core Demo

**Personal AI assistant project • Python • SQLite • Tool execution • Work in progress**

This repository is a **curated, runnable excerpt of the actual Maddy codebase**,
prepared as a technical portfolio demonstration. It is **not the full Maddy assistant**
and does **not** claim to provide a working language model, voice interface or smart-home integration.

## What is Maddy?

Maddy is a personal assistant project built primarily with Python. Its broader
(private) codebase includes experimental modules for a local API, LLM integration,
memory, tools, voice, vision and connected devices. Those modules are at different
stages of development and are **not distributed in this excerpt**.

This public technical demo reuses selected real modules to demonstrate three
specific, reproducible engineering behaviors:

| Feature | Verification |
| --- | --- |
| Persistent memory with SQLite | Save a fact and load it in a fresh store instance |
| Workspace tool | Write a Markdown note, read it back, compare SHA-256 hashes |
| Safe file boundaries | Block traversal, hidden/config paths and Windows drive paths |

No models, credentials, network access, external services or personal data are needed.

## Quick start

Python 3.11+ is required.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m scripts.demo_core
python -m pytest -q
```

The demonstration uses fictional content in a temporary directory and removes
that directory when finished. SQLite connections are explicitly closed to avoid
file-lock errors during cleanup on Windows. It does not start a server or download a model.

## Repository layout

```text
services/core/memory.py                 # Real SQLite persistence module from Maddy
services/core/settings.py               # Selected project configuration class
services/core/tools/base.py             # Maddy tool result definitions
services/core/tools/workspace_tools.py  # Real file-workspace tools, with portable path guard
scripts/demo_core.py                    # Executable, offline integration example
tests/test_core_portfolio.py            # Focused tests of demonstrated behaviors
docs/                                    # Scope and security notes
```

## Source and changes

Core modules were extracted from the creator's private Maddy repository. This
portfolio copy makes targeted changes: generic device labels in `settings.py`,
a **cross-platform path validation fix** in `workspace_tools.py`, and explicit
SQLite connection cleanup in `memory.py` for Windows compatibility. These changes
are covered by regression tests. The original working project has not been modified.

## Known limitations

- This is **not an AI chat demo**. The Python core behaviors above are real; a
  local language model is not included or simulated.
- The original full web UI, model and device integrations are not included.
- Additional testing and hardening are needed before connecting file tools to
  untrusted inputs or exposing them as a service.
- Maddy remains a personal project in active development.

## Privacy and publishing

No private `.env` files, personal databases, message histories, model weights,
personal README, device credentials or homelab configs are included. See
`docs/SECURITY.md`. This repository contains **no redistribution license**;
its author can choose a license before publishing.
