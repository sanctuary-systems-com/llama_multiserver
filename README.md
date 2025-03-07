# Llama multiserver

A proxy server and process manager for on-demand loading and unloading of single-model runners like Llama.cpp and vLLM to efficiently serve multiple models.

Combines the performance and GPU support of runners like Llama.cpp and vLLM with the dynamic model loading of apps like Ollama and LM Studio.

## Why

Because Ollama only cares about CUDA and ROCm wich makes my Intel GPU sad.

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
  "model": "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
  "prompt": "Write a report on the financials of Apple Inc.",
  "max_tokens": 128,
  "temperature": 0
}'
```
