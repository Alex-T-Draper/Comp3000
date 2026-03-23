# test_models.py
"""
Model comparison testing script for dissertation
Compare different summarization models across multiple ToS documents
"""

import json
import os
import time
import torch
from nlp_service import (
    compare_summarization_models,
    abstractive_summary,
    SUMMARIZATION_MODELS,
    _model_cache
)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def detect_device():
    """Detect available compute device and print GPU info if available"""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
        print(f"GPU detected: {gpu_name} ({gpu_mem} GB)")
        print(f"CUDA version: {torch.version.cuda}")
        return "cuda"
    else:
        print("No CUDA GPU detected — running on CPU only.")
        return None

# ToS documents to test against (filename without extension -> display label)
TOS_DOCUMENTS = {
    "ecommerce_tos": "E-Commerce (BazaarBox)",
    "cloudstorage_tos": "Cloud Storage (VaultDrive)",
    "socialmedia_tos": "Social Media (ConnectSphere)",
    "education_tos": "Education (LearnVault)",
    "fitness_tos": "Fitness (PulseFit)",
    "musicstreaming_tos": "Music Streaming (SonicWave)",
}

def load_tos_text(filename: str) -> str:
    """Load a ToS text file from the NLP directory"""
    filepath = os.path.join(os.path.dirname(__file__), "tos_documents", f"{filename}.txt")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {filepath} not found")
        return ""

def load_all_documents() -> dict:
    """Load all ToS documents, returning {filename: text}"""
    docs = {}
    for filename in TOS_DOCUMENTS:
        text = load_tos_text(filename)
        if text:
            docs[filename] = text
        else:
            print(f"  Skipping {filename} (could not load)")
    return docs

def test_single_model(text: str, model_name: str):
    """Test a single model on one document"""
    print(f"\n{'='*60}")
    print(f"Testing Model: {model_name}")
    print(f"Model Path: {SUMMARIZATION_MODELS.get(model_name, 'Unknown')}")
    print(f"{'='*60}")

    try:
        start = time.time()
        summary = abstractive_summary(text, model_name=model_name)
        elapsed = round(time.time() - start, 2)
        print(f"\nSummary:\n{summary}")
        print(f"\nWord count: {len(summary.split())}  |  Time: {elapsed}s")
        return summary
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_all_models_single_doc(text: str, doc_label: str):
    """Test all models on a single document, returning per-model results"""
    print(f"\n{'='*80}")
    print(f"DOCUMENT: {doc_label}")
    print(f"Input length: {len(text.split())} words")
    print(f"{'='*80}")

    results = {}
    for model_name in SUMMARIZATION_MODELS:
        try:
            start = time.time()
            summary = abstractive_summary(text, model_name=model_name)
            elapsed = round(time.time() - start, 2)
            word_count = len(summary.split())
            results[model_name] = {
                "summary": summary,
                "summary_length": word_count,
                "compression_ratio": round(word_count / len(text.split()), 4),
                "time_seconds": elapsed,
            }
            print(f"  {model_name}: {word_count} words, {elapsed}s")
        except Exception as e:
            results[model_name] = {"error": str(e)}
            print(f"  {model_name}: ERROR - {e}")

    return results

def test_all_models_all_docs(output_file: str = os.path.join(RESULTS_DIR, "model_comparison_results.json")):
    """
    Run every model against every ToS document.
    Produces per-document results and aggregate statistics per model.
    """
    docs = load_all_documents()
    if not docs:
        print("No documents loaded — aborting.")
        return None

    print(f"\nLoaded {len(docs)} documents, testing {len(SUMMARIZATION_MODELS)} models")
    print(f"Total runs: {len(docs) * len(SUMMARIZATION_MODELS)}\n")

    all_results = {}
    for filename, text in docs.items():
        label = TOS_DOCUMENTS[filename]
        doc_results = test_all_models_single_doc(text, label)
        all_results[filename] = {
            "label": label,
            "input_word_count": len(text.split()),
            "models": doc_results,
        }

    # ---- Aggregate statistics per model ----
    aggregates = {}
    for model_name in SUMMARIZATION_MODELS:
        lengths = []
        ratios = []
        times = []
        errors = 0
        for doc_data in all_results.values():
            m = doc_data["models"].get(model_name, {})
            if "error" in m:
                errors += 1
            else:
                lengths.append(m["summary_length"])
                ratios.append(m["compression_ratio"])
                times.append(m["time_seconds"])

        if lengths:
            aggregates[model_name] = {
                "avg_summary_length": round(sum(lengths) / len(lengths), 1),
                "avg_compression_ratio": round(sum(ratios) / len(ratios), 4),
                "avg_time_seconds": round(sum(times) / len(times), 2),
                "documents_succeeded": len(lengths),
                "documents_failed": errors,
            }
        else:
            aggregates[model_name] = {"documents_failed": errors}

    # ---- Print aggregate table ----
    print(f"\n{'='*80}")
    print("AGGREGATE RESULTS ACROSS ALL DOCUMENTS")
    print(f"{'='*80}\n")
    print(f"{'Model':<25} {'Avg Words':>10} {'Avg Ratio':>10} {'Avg Time':>10} {'OK':>4} {'Fail':>4}")
    print("-" * 70)
    for model_name, agg in aggregates.items():
        if "avg_summary_length" in agg:
            print(
                f"{model_name:<25} "
                f"{agg['avg_summary_length']:>10} "
                f"{agg['avg_compression_ratio']:>10.4f} "
                f"{agg['avg_time_seconds']:>9}s "
                f"{agg['documents_succeeded']:>4} "
                f"{agg['documents_failed']:>4}"
            )
        else:
            print(f"{model_name:<25} {'—':>10} {'—':>10} {'—':>10} {'0':>4} {agg['documents_failed']:>4}")

    # ---- Save full results ----
    output = {
        "documents_tested": len(docs),
        "models_tested": len(SUMMARIZATION_MODELS),
        "per_document": all_results,
        "aggregate": aggregates,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nFull results saved to: {output_file}")
    return output

def compare_two_models(model1: str, model2: str):
    """Compare two models side-by-side across all documents"""
    docs = load_all_documents()

    print(f"\n{'='*80}")
    print(f"COMPARING: {model1}  vs  {model2}")
    print(f"{'='*80}")

    for filename, text in docs.items():
        label = TOS_DOCUMENTS[filename]
        print(f"\n--- {label} ({len(text.split())} words) ---")

        s1 = abstractive_summary(text, model_name=model1)
        s2 = abstractive_summary(text, model_name=model2)

        print(f"\n  {model1} ({len(s1.split())} words):")
        print(f"    {s1[:150]}...")
        print(f"\n  {model2} ({len(s2.split())} words):")
        print(f"    {s2[:150]}...")

def test_cpu_vs_gpu(model_names=None, doc_filename="ecommerce_tos",
                    output_file=os.path.join(RESULTS_DIR, "cpu_vs_gpu_results.json")):
    """
    Benchmark each model on both CPU and GPU for a single document.
    Prints a side-by-side timing comparison and saves results to JSON.
    """
    gpu_device = detect_device()
    if gpu_device is None:
        print("\nGPU not available — cannot run CPU vs GPU comparison.")
        return None

    text = load_tos_text(doc_filename)
    if not text:
        return None

    if model_names is None:
        model_names = list(SUMMARIZATION_MODELS.keys())

    label = TOS_DOCUMENTS.get(doc_filename, doc_filename)
    print(f"\n{'='*80}")
    print(f"CPU vs GPU BENCHMARK — {label} ({len(text.split())} words)")
    print(f"{'='*80}")

    results = {}
    for model_name in model_names:
        print(f"\n--- {model_name} ---")
        row = {}
        for device in ["cpu", "cuda"]:
            try:
                # Warm-up run (load model, JIT compile kernels)
                abstractive_summary(text, model_name=model_name, device=device)
                # Timed run
                if device == "cuda":
                    torch.cuda.synchronize()
                start = time.time()
                summary = abstractive_summary(text, model_name=model_name, device=device)
                if device == "cuda":
                    torch.cuda.synchronize()
                elapsed = round(time.time() - start, 2)
                row[device] = {
                    "summary_length": len(summary.split()),
                    "time_seconds": elapsed,
                }
                print(f"  {device.upper():>5}: {elapsed}s  ({len(summary.split())} words)")
            except Exception as e:
                row[device] = {"error": str(e)}
                print(f"  {device.upper():>5}: ERROR — {e}")

        if "time_seconds" in row.get("cpu", {}) and "time_seconds" in row.get("cuda", {}):
            speedup = round(row["cpu"]["time_seconds"] / row["cuda"]["time_seconds"], 2)
            row["gpu_speedup"] = speedup
            print(f"  Speedup: {speedup}x")

        results[model_name] = row

        # Free GPU memory before loading the next model
        cache_key = f"{model_name}@cuda"
        if cache_key in _model_cache:
            del _model_cache[cache_key]
        torch.cuda.empty_cache()

    # ---- Summary table ----
    print(f"\n{'='*80}")
    print(f"{'Model':<25} {'CPU (s)':>10} {'GPU (s)':>10} {'Speedup':>10}")
    print("-" * 60)
    for model_name, row in results.items():
        cpu_t = row.get("cpu", {}).get("time_seconds", "—")
        gpu_t = row.get("cuda", {}).get("time_seconds", "—")
        spd = row.get("gpu_speedup", "—")
        print(f"{model_name:<25} {str(cpu_t):>10} {str(gpu_t):>10} {str(spd) + 'x' if spd != '—' else '—':>10}")

    # ---- Save ----
    output = {
        "document": doc_filename,
        "gpu": torch.cuda.get_device_name(0),
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {output_file}")
    return output


if __name__ == "__main__":
    gpu_device = detect_device()

    # Run full comparison across all documents and models (CPU)
    results = test_all_models_all_docs()

    # If GPU is available, also run CPU vs GPU benchmark
    if gpu_device:
        test_cpu_vs_gpu()

    # Test a single model on one document
    # text = load_tos_text("ecommerce_tos")
    # test_single_model(text, "distilbart-cnn-12-6")

    # Compare two models across all documents
    # compare_two_models("distilbart-cnn-12-6", "bart-large-cnn")
