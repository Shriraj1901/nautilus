import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from zimscraperlib.constants import DEFAULT_USER_AGENT

from nautiluszim.scraper import Nautilus


@pytest.fixture
def user_agent_server():
    """Local HTTP server recording the User-Agent of each request it receives"""
    seen: list[str | None] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen.append(self.headers.get("User-Agent"))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *_args, **_kwargs):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}", seen
    server.shutdown()
    server.server_close()
    thread.join()


def test_collection_urls_check_sends_scraperlib_user_agent(user_agent_server, tmp_path):
    base_url, seen = user_agent_server
    collection = tmp_path / "collection.json"
    collection.write_text(
        json.dumps([{"title": "t", "files": [{"url": f"{base_url}/file.txt"}]}])
    )
    scraper = Nautilus(
        archive="",
        collection=str(collection),
        nb_items_per_page=10,
        no_random=True,
        show_description=True,
        output_dir=str(tmp_path / "out"),
        fname="test.zim",
        debug=False,
        keep_build_dir=False,
        language="eng",
        locale_name="en",
        tags="test",
        name="test",
        title="test",
        creator="test",
        publisher="test",
    )

    scraper.test_all_urls()

    assert seen == [DEFAULT_USER_AGENT]
