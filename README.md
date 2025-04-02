# Llama multiserver

A proxy server and process manager for on-demand loading and unloading of Llama.cpp to efficiently serve multiple models.

Combines the performance and GPU support of Llama.cpp with the dynamic model loading of apps like Ollama and LM Studio.

## Why

Because Ollama only cares about CUDA and ROCm wich makes my Intel GPU sad.

## Usage

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
