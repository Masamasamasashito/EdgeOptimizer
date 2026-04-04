import asyncio
import aiohttp
import time
import logging

logger = logging.getLogger(__name__)

class LLMProbe:
    def __init__(self, endpoint_config, session):
        self.id = endpoint_config['id']
        self.url = endpoint_config['url']
        self.model = endpoint_config.get('model', 'default')
        self.api_key = endpoint_config.get('api_key', 'EMPTY')
        self.session = session

    async def measure(self, prompt, timeout_seconds=120):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.get("system", "You are a helpful assistant.")},
                {"role": "user", "content": prompt.get("user", "Hello")}
            ],
            "stream": True,
            "max_tokens": 512
        }

        start_time = time.time()
        ttft = None
        output_chunks = 0
        
        metrics = {
            "engine": self.id,
            "success": False,
            "error": None,
            "ttft_ms": 0,
            "e2e_ms": 0,
            "tps": 0.0,
            "output_tokens": 0
        }

        try:
            # Note: We use a larger timeout here specifically to accommodate long queues under concurrency
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with self.session.post(self.url, headers=headers, json=payload, timeout=timeout) as response:
                response.raise_for_status()

                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data:"):
                            if line_str == "data: [DONE]":
                                break
                            
                            # First chunk marks TTFT
                            if ttft is None:
                                ttft = time.time() - start_time
                            
                            output_chunks += 1
                            
                end_time = time.time()
                total_time = end_time - start_time
                
                # If no TTFT recorded but request succeeded, fallback
                if ttft is None:
                    ttft = total_time

                metrics["success"] = True
                metrics["ttft_ms"] = ttft * 1000
                metrics["e2e_ms"] = total_time * 1000
                metrics["output_tokens"] = output_chunks
                
                # Calculate TPS (Tokens per second after first token)
                time_generating = total_time - ttft
                if time_generating > 0 and output_chunks > 1:
                    # Subtract 1 token because the first token is part of TTFT
                    metrics["tps"] = (output_chunks - 1) / time_generating

        except Exception as e:
            metrics["error"] = str(e)
            
        return metrics

class BenchRunner:
    def __init__(self, config):
        self.settings = config.get("settings", {})
        self.concurrency = self.settings.get("concurrency", 1)
        self.timeout = self.settings.get("timeout_seconds", 120)
        self.endpoints = [ep for ep in config.get("endpoints", []) if ep.get("enabled", False)]

    async def run_benchmark(self, prompts):
        all_results = []
        
        # We process engine by engine so they don't interfere mechanically
        for ep_config in self.endpoints:
            logger.info(f"--- Benchmarking Engine: {ep_config['id']} // Concurrency: {self.concurrency} ---")
            
            async with aiohttp.ClientSession() as session:
                probe = LLMProbe(ep_config, session)
                semaphore = asyncio.Semaphore(self.concurrency)
                
                async def bound_measure(prompt):
                    async with semaphore:
                        return await probe.measure(prompt, self.timeout)
                
                tasks = [bound_measure(p) for p in prompts]
                results = await asyncio.gather(*tasks)
                all_results.extend(results)
                
        return all_results
