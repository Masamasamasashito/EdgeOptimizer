import argparse
import asyncio
import json
import yaml
import os
import logging
from probe import BenchRunner
from reporter import Reporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="EdgeOptimizer LLM Bench Probe")
    parser.add_argument("--config", type=str, default="bench_config.yaml", help="Path to the config file")
    args = parser.parse_args()

    # Load Config
    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        return

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # Load Prompts
    dataset_path = config["settings"].get("dataset_path", "./datasets/sample_prompts.jsonl")
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset file not found: {dataset_path}")
        return
        
    prompts = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))
                
    limit = config["settings"].get("limit_requests", 0)
    if limit > 0:
        prompts = prompts[:limit]

    logger.info(f"Loaded {len(prompts)} prompts from {dataset_path}")

    # Initialize Runner
    runner = BenchRunner(config)
    
    # Run Benchmark
    logger.info("Starting Benchmark...")
    results = await runner.run_benchmark(prompts)
    logger.info(f"Benchmark completed. Captured {len(results)} metrics.")

    # Generate Report
    reporter = Reporter(results, config)
    reporter.generate_report()

if __name__ == "__main__":
    asyncio.run(main())
