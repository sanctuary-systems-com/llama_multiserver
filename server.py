import aiohttp
from aiohttp import web
import subprocess
import asyncio
import psutil
import sys
import json
import os
import pathlib
from urllib.parse import urlparse

class Runner:
    def __init__(self, name, port=8234, host="localhost"):
        global timeout

        self.name = name
        self.port = port
        self.host = host
        self.loop = asyncio.get_running_loop()

        cmd = [
            "llama-server",
            "--host", host,
            "--port", str(port),
            "--hf-repo", name,
            "--gpu-layers", "999",
            "--jinja",
            "--no-warmup",
        ]
        self.proc = subprocess.Popen(cmd)

        if timeout:
            self.keepalive()
            self._timeout()
    
    def _timeout(self):
        if self.stop_at < self.loop.time():
            self.terminate()
        else:
            self.timer = self.loop.call_at(self.stop_at, self._timeout)
    
    def keepalive(self):
        global timeout
        self.stop_at = self.loop.time()+timeout

    def terminate(self):
        if hasattr(self, "timer"):
            self.timer.cancel()
        print("stopping runner for", self.name)
        self.proc.terminate()
    
    async def online(self):
        while True:
            if self.proc.poll() != None:
                return False
            ps = psutil.Process(self.proc.pid)
            conn = ps.net_connections()
            print(conn)
            for sock in  conn:
                if sock.laddr.port == self.port:
                    return True
            await asyncio.sleep(1)


active_runner = None

async def forward_request(request):
    global active_runner
    model = (await request.json())["model"]
    print(active_runner)
    if active_runner == None or active_runner.name != model or not await active_runner.online():
        if active_runner != None:
            active_runner.terminate()
        active_runner = Runner(model)
        await active_runner.online()
    active_runner.keepalive()

    target_url = f"http://{active_runner.host}:{active_runner.port}/{request.match_info['tail']}"
    print(target_url)

    data = await request.read()
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.request(method=request.method,
                                    url=target_url,
                                    headers=request.headers,
                                    data=data) as req:

                if req.status == 503:
                    req.close()
                    await asyncio.sleep(1)
                    continue

                resp = web.StreamResponse(status=req.status, reason=req.reason)
                resp.headers.update(resp.headers)
                await resp.prepare(request)
                async for chunk in req.content.iter_any():
                    await resp.write(chunk)
                await resp.write_eof()
                return resp

# Check environment variables for cache location
if "XDG_CACHE_HOME" in os.environ:
    cache_dir = os.path.join(os.environ["XDG_CACHE_HOME"], "llama.cpp")
elif "LOCALAPPDATA" in os.environ:
    cache_dir = os.path.join(os.environ["LOCALAPPDATA"], "llama.cpp")
else:
    cache_dir = os.path.expanduser("~/.cache/llama.cpp")
cache_path = pathlib.Path(cache_dir)

async def models_request(request):
    model_ids = []

    # Get all JSON files in the cache directory
    if cache_path.exists():
        for file_path in cache_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    url = data["url"]

                    parsed_url = urlparse(url)
                    path_parts = parsed_url.path.strip('/').split('/')

                    model_id = f"{path_parts[0]}/{path_parts[1]}"
                    model_ids.append(model_id)
            except:
                # Skip any files with errors
                continue

    return web.json_response(
        {"object": "list",
         "data": [{"id": k, "object": "model"} for k in model_ids]}
    )


routes = [
    web.route('GET', '/v1/models', models_request),
    web.route('*', '/{tail:.*}', forward_request),
]

app = web.Application()
app.add_routes(routes)

timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 0

web.run_app(app, host='0.0.0.0', port=8765)
