import asyncio
from pathlib import Path

from services.core.memory import MemoryStore
from services.core.settings import Settings
from services.core.tools.workspace_tools import WorkspaceCreateFileTool, WorkspaceReadFileTool


def test_sqlite_fact_survives_new_connection(tmp_path):
    database = tmp_path / 'memory.sqlite3'
    MemoryStore(database).set_fact('topic', 'demo')
    assert MemoryStore(database).get_fact('topic') == 'demo'


def test_write_read_sha_verification(tmp_path):
    async def scenario():
        opts = Settings(_env_file=None, workspace_root=tmp_path)
        writer = WorkspaceCreateFileTool(opts)
        reader = WorkspaceReadFileTool(opts)
        result = await writer.run({'path': 'notes/test.md', 'content': 'demo'})
        assert result.data['confirmed'] is True
        reread = await reader.run({'path': 'notes/test.md'})
        assert reread.data['sha256'] == result.data['sha256']
        assert reread.data['content'] == 'demo'
    asyncio.run(scenario())


def test_blocked_paths_including_windows_drive_on_posix(tmp_path):
    async def scenario():
        writer=WorkspaceCreateFileTool(Settings(_env_file=None,workspace_root=tmp_path))
        for path in ['../escape.md','C:/escape.md',r'C:\escape.md',r'..\escape.md','.env','.git/config.txt','data/private.txt']:
            result=await writer.run({'path':path,'content':'unsafe'})
            assert result.data['confirmed'] is False, path
    asyncio.run(scenario())


def test_duplicate_create_cannot_overwrite(tmp_path):
    async def scenario():
        writer=WorkspaceCreateFileTool(Settings(_env_file=None,workspace_root=tmp_path))
        first=await writer.run({'path':'note.md','content':'original'})
        second=await writer.run({'path':'note.md','content':'replacement'})
        assert first.data['confirmed'] is True
        assert second.data['confirmed'] is False
        assert (tmp_path/'note.md').read_text()=='original'
    asyncio.run(scenario())


def test_memory_connection_is_closed_on_context_exit(tmp_path):
    import sqlite3
    store = MemoryStore(tmp_path / 'connection-check.sqlite3')
    with store._connect() as connection:
        assert connection.execute('SELECT 1').fetchone() == (1,)
    try:
        connection.execute('SELECT 1')
    except sqlite3.ProgrammingError as exc:
        assert 'closed' in str(exc).lower()
    else:
        raise AssertionError('SQLite connection remained open after use')


def test_memory_connection_closes_on_exception(tmp_path):
    import sqlite3
    store = MemoryStore(tmp_path / 'exception-check.sqlite3')
    try:
        with store._connect() as connection:
            raise RuntimeError('simulated failure')
    except RuntimeError:
        pass
    try:
        connection.execute('SELECT 1')
    except sqlite3.ProgrammingError:
        pass
    else:
        raise AssertionError('SQLite connection remained open after failure')
