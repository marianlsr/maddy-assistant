"""Real, offline technical demonstration using selected Maddy core modules.

Does NOT use any language model or home/network integration.
"""
from __future__ import annotations

import argparse
import asyncio
import tempfile
from pathlib import Path

from services.core.memory import MemoryStore
from services.core.settings import Settings
from services.core.tools.workspace_tools import (
    WorkspaceCreateFileTool,
    WorkspaceReadFileTool,
)


async def run_demo(root: Path) -> None:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    settings = Settings(_env_file=None, workspace_root=root)
    memory_path = root / 'example-memory.sqlite3'
    memory = MemoryStore(memory_path)
    memory.set_fact('demo.project', 'Aurora')
    memory.set_fact('demo.todo', 'Review project notes')

    # A second instance validates SQLite persistence across object reinitialization.
    reopened = MemoryStore(memory_path)
    assert reopened.get_fact('demo.project') == 'Aurora'
    print('[PASS] Persistent SQLite memory survived reopening the store')

    writer = WorkspaceCreateFileTool(settings)
    reader = WorkspaceReadFileTool(settings)
    relative_path = 'notes/aurora.md'
    initial = await writer.run({'path':relative_path,'content':'# Aurora\n- Review project notes\n'})
    assert initial.data.get('confirmed'),initial.text
    observed = await reader.run({'path':relative_path})
    assert observed.data['sha256'] == initial.data['sha256']
    print('[PASS] Workspace file created, read back, and SHA256 verified')

    # An unsafe target is rejected without touching the filesystem outside root.
    for invalid in ('../outside.md','C:/outside.md','.env'):
        denied = await writer.run({'path':invalid,'content':'DO NOT WRITE'})
        assert denied.data.get('confirmed') is False, invalid
    print('[PASS] Unsafe paths rejected, including Windows paths on Linux')
    print('Maddy core demonstration completed with fictional data, entirely offline.')
    print('NOTE: This is a curated core-module demo, not the complete AI assistant.')


def main() -> None:
    parser=argparse.ArgumentParser(description='Run the Maddy core technical demonstration.')
    parser.add_argument('--workspace',type=Path,help='Optional local demo folder (must be empty)')
    args=parser.parse_args()
    if args.workspace is not None:
        if args.workspace.exists() and any(args.workspace.iterdir()):
            parser.error('--workspace must be an empty folder to avoid overwriting data')
        asyncio.run(run_demo(args.workspace))
    else:
        with tempfile.TemporaryDirectory(prefix='maddy-core-demo-') as tmp:
            asyncio.run(run_demo(Path(tmp)))

if __name__=='__main__':
    main()
