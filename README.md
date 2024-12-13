# Llama multiserver

A proxy and process manager for single-model runners like Llama.cpp and vLLM.

Runners like Llama.cpp and vLLM have wide support for different GPUs, but the projects that use them like Ollama frequently only support modern NVIDIA and AMD cards. This leaves users of Intel or older AMD cards with [stale PRs](https://github.com/ollama/ollama/pull/5059) and [outdated forks](https://github.com/intel-analytics/ipex-llm/issues/12370).

On the other hand, Llama.cpp and vLLM only support running a single model that is kept in memory perpetually. That makes them unsuitable to serve a variety of models in the background on the average desktop.

This project is a proxy that will start configured runners on demand, and terminate them when idle.

## Usage

Creat `runners.toml` (`key = value` becomes `--key value`):

```toml
timeout = 300

["llama3.1:latest"]
gpu-layers = 999
model = "/path/to/Meta-Llama-3.1-8B-Instruct-Q4_K_S.gguf"

["Qwen/Qwen2.5-coder-3B"]
exec = ["vllm", "serve", "Qwen/Qwen2.5-coder-3B"]
gpu-memory-utilization = 0.5
max-model-len = 4096
port = 8900
```

Install dependencies:

```
pip install aiohttp psutil
```

Run:

```
python server.py
```

Test:

```
curl http://localhost:8765/v1/completions -H "Content-Type: application/json" -d '{
  "model": "llama3.1:latest",
  "prompt": "Write a report on the financials of Apple Inc.",
  "max_tokens": 1024,
  "temperature": 0
}'
```
