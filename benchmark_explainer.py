import os
import time
import subprocess
import json
import shutil
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PARSER_SCRIPT = os.path.join(BACKEND_DIR, "parser", "parser.py")
CLUSTERING_SCRIPT = os.path.join(BACKEND_DIR, "clustering", "run_clustering.py")
EXPLAINER_SCRIPT = os.path.join(BACKEND_DIR, "explainer", "explainer.py")
CACHE_FILE = os.path.join(BACKEND_DIR, "explainer", "explainer_cache.json")

REPO_URL = "https://github.com/JacMattisen/board-java.git"
TARGET_DIR = os.path.join(BACKEND_DIR, "temp_repos", "board-java-benchmark")

# Models to benchmark with varied workers
OPENROUTER_MODELS = [
    "openrouter-openai/gpt-oss-20b:free",
    "openrouter-stepfun/step-3.5-flash:free"
]

# Worker counts to test for the concurrency benchmark
WORKER_COUNTS = [1, 2, 4, 8]
CONCURRENCY_MODEL = "openrouter-stepfun/step-3.5-flash:free"

def run_command(command, cwd=None):
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        out, _ = process.communicate()
        if process.returncode != 0:
            return False, out
        return True, out
    except Exception as e:
        return False, str(e)

def setup_baseline():
    print("--- Setting up Baseline for Explainer Benchmark ---")
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)

    print("Cloning repository...")
    run_command(["git", "clone", "--depth", "1", REPO_URL, TARGET_DIR])

    print("Running Parser...")
    parser_cwd = os.path.dirname(PARSER_SCRIPT)
    run_command([sys.executable, "parser.py", TARGET_DIR, "--json", "graph.json"], cwd=parser_cwd)

    print("Running Clustering...")
    clustering_cwd = os.path.dirname(CLUSTERING_SCRIPT)
    run_command([sys.executable, "run_clustering.py"], cwd=clustering_cwd)

    print("Baseline setup complete.\n")

def run_explainer(model, workers):
    """Clear cache and run explainer, returning (success, elapsed_time)."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

    explainer_cwd = os.path.dirname(EXPLAINER_SCRIPT)
    start_time = time.time()
    success, out = run_command(
        [sys.executable, "explainer.py", "--model", model, "--workers", str(workers)],
        cwd=explainer_cwd
    )
    elapsed = time.time() - start_time
    if not success:
        print(f"  FAILED! Output:\n{out[:500]}")
    return success, elapsed

def main():
    setup_baseline()

    model_results = []
    worker_results = []

    # --- Part 1: Model Comparison (fixed workers=4) ---
    print("=" * 60)
    print("PART 1: Model Comparison (workers=4)")
    print("=" * 60)

    for model in OPENROUTER_MODELS:
        print(f"  Benchmarking: {model} ...")
        success, elapsed = run_explainer(model, workers=4)
        status = "success" if success else "failed"
        print(f"  Done in {elapsed:.2f}s — {status}")
        model_results.append({"model": model, "workers": 4, "time_s": elapsed, "status": status})

    # --- Part 2: Concurrency Comparison (fixed model = step-3.5-flash) ---
    print()
    print("=" * 60)
    print(f"PART 2: Workers Comparison ({CONCURRENCY_MODEL})")
    print("=" * 60)

    for workers in WORKER_COUNTS:
        print(f"  Benchmarking: workers={workers} ...")
        success, elapsed = run_explainer(CONCURRENCY_MODEL, workers=workers)
        status = "success" if success else "failed"
        print(f"  Done in {elapsed:.2f}s — {status}")
        worker_results.append({"model": CONCURRENCY_MODEL, "workers": workers, "time_s": elapsed, "status": status})

    # --- Print Summary ---
    print()
    print("=" * 60)
    print("SUMMARY: Model Comparison (workers=4)")
    print("=" * 60)
    print(f"{'Model':<45} | {'Time (s)':<10} | Status")
    print("-" * 68)
    for r in model_results:
        print(f"{r['model']:<45} | {r['time_s']:<10.2f} | {r['status']}")

    print()
    print("=" * 60)
    print(f"SUMMARY: Workers Comparison ({CONCURRENCY_MODEL.split('/')[-1]})")
    print("=" * 60)
    print(f"{'Workers':<10} | {'Time (s)':<10} | Status")
    print("-" * 35)
    for r in worker_results:
        print(f"{r['workers']:<10} | {r['time_s']:<10.2f} | {r['status']}")

    # Save all results
    all_results = {"model_comparison": model_results, "worker_comparison": worker_results}
    with open("benchmark_explainer_results.json", "w") as f:
        json.dump(all_results, f, indent=4)
    print("\nResults saved to benchmark_explainer_results.json")

if __name__ == "__main__":
    main()
