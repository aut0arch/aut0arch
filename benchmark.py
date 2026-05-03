import os
import time
import subprocess
import json
import shutil
import uuid
import sys

# Define base paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PARSER_SCRIPT = os.path.join(BACKEND_DIR, "parser", "parser.py")
CLUSTERING_SCRIPT = os.path.join(BACKEND_DIR, "clustering", "run_clustering.py")
TEMP_DIR = os.path.join(BACKEND_DIR, "temp_repos")
GRAPH_JSON_PATH = os.path.join(BACKEND_DIR, "parser", "graph.json")
CLUSTERED_JSON_PATH = os.path.join(BACKEND_DIR, "clustering", "clustered_structure.json")

REPOSITORIES = [
    "https://github.com/JacMattisen/board-java.git",
    "https://github.com/SaurabhDalavi16/Java-Project.git",
    "https://github.com/TheAlgorithms/Java.git",
]

RESULTS_FILE = os.path.join(BACKEND_DIR, "benchmark_results.json")

def run_command(command, cwd=None):
    """Runs a shell command and returns output."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        output = []
        for line in process.stdout:
            output.append(line)
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command, "".join(output))
        return True, "".join(output)
    except subprocess.CalledProcessError as e:
        return False, e.stdout

def cleanup(target_dir):
    if os.path.exists(target_dir):
        try:
            def on_rm_error(func, path, exc_info):
                os.chmod(path, 0o777)
                func(path)
            shutil.rmtree(target_dir, onerror=on_rm_error)
        except Exception as e:
            print(f"Failed to cleanup {target_dir}: {e}")

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    results = []

    for repo_url in REPOSITORIES:
        print(f"\n--- Benchmarking {repo_url} ---")
        run_id = str(uuid.uuid4())[:8]
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_dir = os.path.join(TEMP_DIR, f"{repo_name}_{run_id}")
        
        repo_result = {
            "repository": repo_name,
            "url": repo_url,
            "loc": 0,
            "files": 0,
            "nodes": 0,
            "edges": 0,
            "clusters": 0,
            "clone_time_s": None,
            "parser_time_s": None,
            "clustering_time_s": None,
            "status": "success",
            "error_stage": None
        }

        try:
            # 1. Clone
            print(f"Cloning to {target_dir}...")
            start_time = time.time()
            success, out = run_command(["git", "clone", "--depth", "1", repo_url, target_dir])
            repo_result["clone_time_s"] = time.time() - start_time
            if not success:
                print(f"Failed to clone: {out}")
                repo_result["status"] = "failed"
                repo_result["error_stage"] = "clone"
                results.append(repo_result)
                continue
                
            # Count LOC and Java Files
            loc = 0
            files_count = 0
            for root, _, files in os.walk(target_dir):
                for f in files:
                    if f.endswith(".java"):
                        files_count += 1
                        try:
                            with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as code_file:
                                loc += sum(1 for _ in code_file)
                        except Exception:
                            pass
            repo_result["loc"] = loc
            repo_result["files"] = files_count

            # 2. Parse
            print("Running Parser...")
            parser_cwd = os.path.dirname(PARSER_SCRIPT)
            python_exe = sys.executable 
            start_time = time.time()
            success, out = run_command([python_exe, "parser.py", target_dir, "--json", "graph.json"], cwd=parser_cwd)
            repo_result["parser_time_s"] = time.time() - start_time
            
            if os.path.exists(GRAPH_JSON_PATH):
                with open(GRAPH_JSON_PATH, 'r', encoding='utf-8') as gf:
                    g_data = json.load(gf)
                    repo_result["nodes"] = len(g_data.get("nodes", []))
                    repo_result["edges"] = len(g_data.get("edges", []))
            
            if not success:
                print(f"Parser failed: {out}")
                repo_result["status"] = "failed"
                repo_result["error_stage"] = "parser"
                results.append(repo_result)
                cleanup(target_dir)
                continue

            # 3. Cluster
            print("Running Clustering...")
            clustering_cwd = os.path.dirname(CLUSTERING_SCRIPT)
            start_time = time.time()
            success, out = run_command([python_exe, "run_clustering.py"], cwd=clustering_cwd)
            repo_result["clustering_time_s"] = time.time() - start_time
            
            if os.path.exists(CLUSTERED_JSON_PATH):
                with open(CLUSTERED_JSON_PATH, 'r', encoding='utf-8') as cf:
                    c_data = json.load(cf)
                    repo_result["clusters"] = len(c_data.get("clusters", []))

            if not success:
                print(f"Clustering failed: {out}")
                repo_result["status"] = "failed"
                repo_result["error_stage"] = "clustering"

        except Exception as e:
            print(f"Unexpected error: {e}")
            repo_result["status"] = "failed"
            repo_result["error_stage"] = "unexpected_error"
        finally:
            results.append(repo_result)
            cleanup(target_dir)

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nBenchmark complete. Results saved to {RESULTS_FILE}")

    # Print summary
    print(f"{'Repository':<20} | {'Files':<5} | {'LOC':<7} | {'Nodes':<5} | {'Edges':<5} | {'Clusters':<8} | {'Parser (s)':<10} | {'Clust. (s)':<10}")
    print("-" * 100)
    for res in results:
        parser = f"{res['parser_time_s']:.2f}" if res['parser_time_s'] else "N/A"
        clust = f"{res['clustering_time_s']:.2f}" if res['clustering_time_s'] else "N/A"
        print(f"{res['repository']:<20} | {res['files']:<5} | {res['loc']:<7} | {res['nodes']:<5} | {res['edges']:<5} | {res['clusters']:<8} | {parser:<10} | {clust:<10}")

if __name__ == "__main__":
    main()
