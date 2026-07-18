from __future__ import annotations

from contextlib import closing
import json
import os
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from graphfakos.desktop import (
    desktop_authorizer,
    generate_desktop_token,
    read_desktop_token_from_fd,
)


def test_generate_desktop_token_is_not_tiny() -> None:
    assert len(generate_desktop_token()) >= 48


def test_read_desktop_token_from_private_pipe() -> None:
    token = generate_desktop_token()
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, token.encode("utf-8"))
        os.close(write_fd)
        write_fd = -1
        assert read_desktop_token_from_fd(read_fd) == token
    finally:
        os.close(read_fd)
        if write_fd >= 0:
            os.close(write_fd)


def test_desktop_authorizer_requires_expected_header() -> None:
    token = generate_desktop_token()
    authorize = desktop_authorizer(token)

    assert authorize("GET", "/explore", {"X-GraphFakos-Desktop-Token": token})
    assert not authorize("GET", "/explore", {})
    assert not authorize("GET", "/explore", {"X-GraphFakos-Desktop-Token": "bad"})
    assert not authorize("DELETE", "/explore", {"X-GraphFakos-Desktop-Token": token})


def test_desktop_backend_emits_readiness_and_authenticates_routes() -> None:
    token = generate_desktop_token()
    read_fd, write_fd = os.pipe()
    os.write(write_fd, token.encode("utf-8"))
    os.close(write_fd)
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "desktop-backend",
            "--token-fd",
            str(read_fd),
        ],
        pass_fds=(read_fd,),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    os.close(read_fd)
    try:
        assert process.stdout is not None
        ready_line = process.stdout.readline().strip()
        ready = json.loads(ready_line)
        assert ready["event"] == "desktop.backend.ready"
        assert ready["host"] == "127.0.0.1"
        assert ready["port"] > 0
        base_url = f"http://{ready['host']}:{ready['port']}"

        with closing(
            urlopen(
                Request(
                    f"{base_url}/explore",
                    headers={"X-GraphFakos-Desktop-Token": token},
                ),
                timeout=5,
            )
        ) as response:
            assert response.status == 200
            assert b"GraphFakos" in response.read()

        try:
            urlopen(Request(f"{base_url}/explore"), timeout=5)
        except HTTPError as exc:
            assert exc.code == 403
        else:
            raise AssertionError("unauthenticated desktop route unexpectedly passed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_desktop_backend_exits_when_token_pipe_is_invalid() -> None:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "graphfakos",
            "desktop-backend",
            "--token-fd",
            "99999",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        for _ in range(20):
            if process.poll() is not None:
                break
            time.sleep(0.05)
        assert process.poll() is not None
        assert process.returncode != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
