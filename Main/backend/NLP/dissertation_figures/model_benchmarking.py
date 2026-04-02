"""Dissertation figures for model selection and GPU vs CPU benchmarking.

Reads:
    output/test_models/cpu_vs_gpu_results.json
    output/test_models/model_comparison_results.json
    output/test_models/rouge_results.json

Produces:
    output/dissertation/gpu_vs_cpu_inference.png
    output/dissertation/model_comparison_time.png
    output/dissertation/model_summary_quality.png
    output/dissertation/gpu_speedup_factor.png
    output/dissertation/rouge_scores.png
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ── paths ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
GPU_CPU_FILE = ROOT / "output" / "test_models" / "cpu_vs_gpu_results.json"
COMPARISON_FILE = ROOT / "output" / "test_models" / "model_comparison_results.json"
ROUGE_FILE = ROOT / "output" / "test_models" / "rouge_results.json"
OUT_DIR = ROOT / "output" / "dissertation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── display names & colours ──────────────────────────────────
MODEL_LABELS = {
    "distilbart-cnn-12-6": "DistilBART",
    "bart-large-cnn": "BART-large",
    "pegasus-cnn": "PEGASUS",
    "t5-base": "T5-base",
    "bart-large-cnn-samsum": "BART-samsum",
    "led-base-16384": "LED-base",
}

# Approximate parameter counts (millions) — from HuggingFace model cards
MODEL_PARAMS = {
    "distilbart-cnn-12-6": 306,
    "bart-large-cnn": 406,
    "pegasus-cnn": 568,
    "t5-base": 220,
    "bart-large-cnn-samsum": 406,
    "led-base-16384": 162,
}

COLOURS = {
    "distilbart-cnn-12-6": "#5B9BD5",
    "bart-large-cnn": "#70AD47",
    "pegasus-cnn": "#FFC000",
    "t5-base": "#ED7D31",
    "bart-large-cnn-samsum": "#A5A5A5",
    "led-base-16384": "#9B59B6",
}

# Preferred model order (selected model first)
MODEL_ORDER = [
    "distilbart-cnn-12-6",
    "bart-large-cnn",
    "pegasus-cnn",
    "t5-base",
    "bart-large-cnn-samsum",
    "led-base-16384",
]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# ── helpers ──────────────────────────────────────────────────
def _save(fig, name):
    path = OUT_DIR / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[OK] {path}")


# ── Figure 1: GPU vs CPU inference time (grouped bar) ───────
def gpu_vs_cpu_chart():
    with open(GPU_CPU_FILE, encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    gpu_name = data.get("gpu", "CUDA GPU")

    models = [m for m in MODEL_ORDER if m in results]
    labels = [MODEL_LABELS[m] for m in models]
    cpu_times = [results[m]["cpu"]["time_seconds"] for m in models]
    gpu_times = [results[m]["cuda"]["time_seconds"] for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars_cpu = ax.bar(x - width / 2, cpu_times, width, label="CPU (Intel i7-11700K)",
                      color="#4472C4", edgecolor="white", linewidth=0.5)
    bars_gpu = ax.bar(x + width / 2, gpu_times, width, label=f"GPU ({gpu_name})",
                      color="#ED7D31", edgecolor="white", linewidth=0.5)

    # Value labels
    for bar in bars_cpu:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{bar.get_height():.1f}s", ha="center", va="bottom", fontsize=9)
    for bar in bars_gpu:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                f"{bar.get_height():.1f}s", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Inference Time (seconds)")
    ax.set_title("GPU vs CPU Inference Time per Model", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend(loc="upper left")
    ax.set_ylim(0, max(cpu_times) * 1.2)

    # 20-second interactive threshold line
    ax.axhline(y=20, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.text(len(models) - 0.5, 20.8, "Interactive threshold (20 s)",
            ha="right", va="bottom", color="red", fontsize=9, fontstyle="italic")

    fig.text(0.5, -0.02,
             "Figure: Inference time comparison on a single ToS document (~1,250 words). "
             "CPU = Intel i7-11700K; GPU = NVIDIA RTX 3080.",
             ha="center", fontsize=9, style="italic")

    fig.tight_layout()
    _save(fig, "gpu_vs_cpu_inference.png")


# ── Figure 2: GPU speedup factor ────────────────────────────
def gpu_speedup_chart():
    with open(GPU_CPU_FILE, encoding="utf-8") as f:
        data = json.load(f)

    results = data["results"]
    models = [m for m in MODEL_ORDER if m in results]
    labels = [MODEL_LABELS[m] for m in models]
    speedups = [results[m]["gpu_speedup"] for m in models]
    colours = [COLOURS[m] for m in models]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels, speedups, color=colours, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, speedups):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}×", ha="left", va="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("GPU Speedup Factor (×)")
    ax.set_title("GPU Speedup Over CPU per Model", fontsize=14, fontweight="bold")
    ax.set_xlim(0, max(speedups) * 1.25)
    ax.invert_yaxis()

    fig.text(0.5, -0.02,
             "Figure: Ratio of CPU to GPU inference time. "
             "Higher values indicate greater benefit from GPU acceleration.",
             ha="center", fontsize=9, style="italic")

    fig.tight_layout()
    _save(fig, "gpu_speedup_factor.png")


# ── Figure 3: Average inference time across all documents ───
def model_comparison_time():
    with open(COMPARISON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    agg = data["aggregate"]
    models = [m for m in MODEL_ORDER if m in agg]
    labels = [MODEL_LABELS[m] for m in models]
    times = [agg[m]["avg_time_seconds"] for m in models]
    colours = [COLOURS[m] for m in models]

    # Also gather per-document times for error bars
    per_doc = data["per_document"]
    model_times = {m: [] for m in models}
    for doc_data in per_doc.values():
        for m in models:
            md = doc_data["models"].get(m, {})
            if "time_seconds" in md:
                model_times[m].append(md["time_seconds"])

    sems = []
    for m in models:
        vals = model_times[m]
        if len(vals) > 1:
            sems.append(np.std(vals, ddof=1) / np.sqrt(len(vals)))
        else:
            sems.append(0)

    x = np.arange(len(models))
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(x, times, color=colours, edgecolor="white", linewidth=0.5,
                  yerr=sems, capsize=4, error_kw={"linewidth": 1.2})

    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + sems[bars.index(bar)] + 0.5,
                f"{t:.1f}s", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_ylabel("Mean Inference Time (seconds)")
    ax.set_title("Mean CPU Inference Time Across All ToS Documents", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0, max(times) * 1.3)

    fig.text(0.5, -0.02,
             f"Figure: Mean inference time (CPU) averaged over {data['documents_tested']} ToS documents. "
             "Error bars show ± SE across documents.",
             ha="center", fontsize=9, style="italic")

    fig.tight_layout()
    _save(fig, "model_comparison_time.png")


# ── Figure 4: Summary quality (length + compression) ───────
def model_summary_quality():
    with open(COMPARISON_FILE, encoding="utf-8") as f:
        data = json.load(f)

    agg = data["aggregate"]
    models = [m for m in MODEL_ORDER if m in agg]
    labels = [MODEL_LABELS[m] for m in models]
    lengths = [agg[m]["avg_summary_length"] for m in models]
    ratios = [agg[m]["avg_compression_ratio"] * 100 for m in models]
    params = [MODEL_PARAMS.get(m, 0) for m in models]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Avg summary length
    colours = [COLOURS[m] for m in models]
    x = np.arange(len(models))

    bars1 = ax1.bar(x, lengths, color=colours, edgecolor="white", linewidth=0.5)
    bars1[0].set_edgecolor("#2E4057")
    bars1[0].set_linewidth(2)
    for bar, v in zip(bars1, lengths):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 f"{v:.0f}", ha="center", va="bottom", fontsize=9)
    ax1.set_ylabel("Mean Summary Length (words)")
    ax1.set_title("Average Summary Length", fontsize=12, fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax1.set_ylim(0, max(lengths) * 1.2)

    # Right: Scatter of params vs time, sized by compression
    times = [agg[m]["avg_time_seconds"] for m in models]
    scatter_colours = [COLOURS[m] for m in models]
    sizes = [r * 15 for r in ratios]  # scale for visibility

    ax2.scatter(params, times, s=sizes, c=scatter_colours,
                edgecolors="black", linewidths=0.8, alpha=0.85, zorder=3)

    for m, p, t in zip(models, params, times):
        ax2.annotate(MODEL_LABELS[m], (p, t),
                     textcoords="offset points", xytext=(8, 4),
                     fontsize=9)

    ax2.set_xlabel("Parameters (millions)")
    ax2.set_ylabel("Mean CPU Inference Time (s)")
    ax2.set_title("Model Size vs Inference Time", fontsize=12, fontweight="bold")
    ax2.set_xlim(0, max(params) * 1.2)
    ax2.set_ylim(0, max(times) * 1.2)
    ax2.grid(True, alpha=0.3)

    fig.text(0.5, -0.02,
             "Figure: Left — mean summary word count across 6 ToS documents. "
             "Right — parameter count vs CPU inference time; bubble size ∝ compression ratio.",
             ha="center", fontsize=9, style="italic")

    fig.tight_layout()
    _save(fig, "model_summary_quality.png")


# ── Figure 5: ROUGE scores (grouped bar) ────────────────────
def rouge_scores_chart():
    with open(ROUGE_FILE, encoding="utf-8") as f:
        data = json.load(f)

    agg = data["aggregate"]
    models = [m for m in MODEL_ORDER if m in agg and agg[m].get("documents_scored", 0) > 0]
    labels = [MODEL_LABELS[m] for m in models]

    r1 = [agg[m]["avg_rouge1_f"] for m in models]
    r2 = [agg[m]["avg_rouge2_f"] for m in models]
    rl = [agg[m]["avg_rougeL_f"] for m in models]

    x = np.arange(len(models))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width, r1, width, label="ROUGE-1", color="#4472C4",
                   edgecolor="white", linewidth=0.5)
    bars2 = ax.bar(x, r2, width, label="ROUGE-2", color="#ED7D31",
                   edgecolor="white", linewidth=0.5)
    bars3 = ax.bar(x + width, rl, width, label="ROUGE-L", color="#70AD47",
                   edgecolor="white", linewidth=0.5)

    # Value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            h = bar.get_height()
            if h > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.008,
                        f"{h:.3f}", ha="center", va="bottom", fontsize=8, rotation=45)

    ax.set_ylabel("F1 Score")
    ax.set_title("ROUGE Scores by Model (vs Extractive Reference)", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.legend(loc="upper right")
    ax.set_ylim(0, max(r1) * 1.35)

    fig.text(0.5, -0.02,
             f"Figure: ROUGE F1 scores averaged over {data['documents_tested']} ToS documents. "
             "Reference = extractive summary (TextRank, 6 sentences).",
             ha="center", fontsize=9, style="italic")

    fig.tight_layout()
    _save(fig, "rouge_scores.png")


# ── main ─────────────────────────────────────────────────────
def main():
    missing = []
    if not GPU_CPU_FILE.exists():
        missing.append(str(GPU_CPU_FILE))
    if not COMPARISON_FILE.exists():
        missing.append(str(COMPARISON_FILE))

    if missing:
        print("[SKIP] Missing benchmark data files:")
        for p in missing:
            print(f"       {p}")
        print("       Run test_models.py first to generate benchmark data.")
        return

    gpu_vs_cpu_chart()
    gpu_speedup_chart()
    model_comparison_time()
    model_summary_quality()

    if ROUGE_FILE.exists():
        rouge_scores_chart()
    else:
        print(f"[SKIP] {ROUGE_FILE} not found — run test_models.py evaluate_rouge() first.")


if __name__ == "__main__":
    main()
