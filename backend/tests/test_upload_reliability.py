import asyncio
import io
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import analyzer, parser
from app.utils import file_handler


@pytest.mark.parametrize('endpoint', ['/api/analyze', '/api/resume/parse'])
def test_upload_size_checked_before_saving(endpoint, monkeypatch):
    monkeypatch.setattr(file_handler, 'MAX_UPLOAD_BYTES', 8)
    monkeypatch.setattr(file_handler, 'save_upload', lambda *a: pytest.fail('oversize data saved'))
    response = TestClient(app).post(endpoint, files={'file': ('resume.txt', b'123456789')})
    assert response.status_code == 413


@pytest.mark.parametrize('filename,content', [('resume.txt', b'  \n\t'), ('resume.pdf', b'bad pdf'), ('resume.docx', b'bad docx')])
def test_empty_or_corrupt_document_is_a_client_error(filename, content, tmp_path, monkeypatch):
    monkeypatch.setattr(file_handler, '_tmp_root', tmp_path)
    response = TestClient(app).post('/api/resume/parse', files={'file': (filename, content)})
    assert response.status_code == 400
    assert not list(tmp_path.iterdir())


def test_utf8_bom_is_removed(tmp_path):
    path = tmp_path / 'resume.txt'
    path.write_bytes('履历内容'.encode('utf-8-sig'))
    assert parser.extract_text(path) == '履历内容'


def test_failure_cleans_temp_file_without_exposing_details(tmp_path, monkeypatch):
    monkeypatch.setattr(file_handler, '_tmp_root', tmp_path)
    def fail(**kwargs):
        raise RuntimeError('private-upstream-details')
    monkeypatch.setattr(analyzer, 'analyze_resume', fail)
    response = TestClient(app).post('/api/analyze', files={'file': ('resume.txt', b'resume')})
    assert response.status_code == 502
    assert 'private-upstream-details' not in response.text
    assert not list(tmp_path.iterdir())


def test_health_remains_responsive_during_analysis(monkeypatch, tmp_path):
    entered, release = threading.Event(), threading.Event()
    def slow_analysis(**kwargs):
        entered.set()
        assert release.wait(5)
        return {'ok': True}
    monkeypatch.setattr(analyzer, 'analyze_resume', slow_analysis)
    monkeypatch.setattr(file_handler, '_tmp_root', tmp_path)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            pending = asyncio.create_task(client.post('/api/analyze', files={'file': ('r.txt', b'resume')}))
            try:
                assert await asyncio.to_thread(entered.wait, 2)
                health = await asyncio.wait_for(client.get('/api/health'), timeout=1)
                assert health.status_code == 200
            finally:
                release.set()
                response = await pending
            assert response.status_code == 200
    asyncio.run(scenario())
