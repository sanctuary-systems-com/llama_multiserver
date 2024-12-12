import aiohttp
from aiohttp import web
import tomllib
import subprocess
import asyncio
import psutil

class Runner:
    def __init__(self, name, args):
        self.name = name
        self.port = args.get("port", 8080)
        self.host = args.get("host", "localhost")
        self.loop = asyncio.get_running_loop()

        binary = args.pop("exec", "llama-server")
        cmd = [binary]
        for k, v in args.items():
            if v == True:
                cmd.append("--"+k)
            else:
                cmd.extend(["--"+k, str(v)])
        self.proc = subprocess.Popen(cmd)

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
        self.timer.cancel()
        print("stopping runner for", self.name)
        self.proc.terminate()
    
    async def online(self):
        ps = psutil.Process(self.proc.pid)
        while True:
            if self.proc.poll() != None:
                return False
            conn = ps.net_connections()
            if conn:
                return True
            await asyncio.sleep(0.01)


active_runner = None

async def forward_request(request):
    global active_runner
    model = (await request.json())["model"]
    print(active_runner)
    if active_runner == None or active_runner.name != model or not await active_runner.online():
        if active_runner != None:
            active_runner.terminate()
        active_runner = Runner(model, runners[model])
        await active_runner.online()
    active_runner.keepalive()

    target_url = f"http://{active_runner.host}:{active_runner.port}/{request.match_info['tail']}"
    print(target_url)

    async with aiohttp.ClientSession() as session:
        async with session.request(method=request.method,
                                   url=target_url,
                                   headers=request.headers,
                                   data=await request.read()) as req:

            resp = web.StreamResponse(status=req.status, reason=req.reason)
            resp.headers.update(resp.headers)
            await resp.prepare(request)
            async for chunk in req.content.iter_any():
                await resp.write(chunk)
            await resp.write_eof()
            return resp

async def models_request(request):
    return web.json_response(
        {"object":"list",
         "data":[{"id":k,"object":"model"} for k in runners.keys()]}
    )


routes = [
    web.route('GET', '/v1/models', models_request),
    web.route('*', '/{tail:.*}', forward_request),
]

app = web.Application()
app.add_routes(routes)

with open("runners.toml", "rb") as f:
    runners = tomllib.load(f)

timeout = runners.pop("timeout", 5*60)

web.run_app(app, host='0.0.0.0', port=8765)
