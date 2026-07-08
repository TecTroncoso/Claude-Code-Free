import os
import subprocess
import sys
import time
import httpx

from tests.conftest import REPO_ROOT, _base_env

def test_translation_anthropic_to_openai():
    """
    Test that the proxy accepts an Anthropic-formatted request, 
    routes it to NVIDIA NIM (OpenAI-compatible), and fails 
    with a 401 Unauthorized from NVIDIA (because of dummy key).
    This proves the translation pipeline works end-to-end.
    """
    env = _base_env()
    # Use a dummy key to guarantee a 401 from NVIDIA if routing works.
    env["NVIDIA_API_KEY"] = "dummy-integration-test-key"
    env["PORT"] = "4001"  # Use a different port to avoid conflicts
    env["PYTHONIOENCODING"] = "utf-8"
    
    import tempfile
    
    log_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
    
    # Start proxy
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=REPO_ROOT,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    
    try:
        # Wait for healthz
        base_url = f"http://127.0.0.1:{env['PORT']}"
        client = httpx.Client(base_url=base_url)
        
        ready = False
        for _ in range(20):
            try:
                resp = client.get("/health")
                if resp.status_code == 200:
                    ready = True
                    break
            except httpx.RequestError:
                pass
            time.sleep(0.5)
            
        if not ready:
            log_file.seek(0)
            logs = log_file.read()
            assert False, f"Proxy failed to boot in time. LOGS:\n{logs}"
        
        # Send an Anthropic request
        response = client.post(
            "/v1/messages",
            headers={
                "x-api-key": "sk-ant-dummy",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "ping"}],
            },
            timeout=10.0
        )
        
        # We expect a 401 Unauthorized because the NVIDIA key is fake.
        # But this means the proxy successfully parsed Anthropic and reached NVIDIA!
        assert response.status_code == 401, f"Expected 401 from upstream, got {response.status_code}. Body: {response.text}"
        
        json_resp = response.json()
        assert "error" in json_resp, "Response should contain an error JSON"
        
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()
