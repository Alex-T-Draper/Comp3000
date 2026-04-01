"""Statistical Tests Summary Table for Dissertation.

Runs key inferential tests across conditions and produces:
- A summary table of test results (PNG image)
- Console output of all statistics

Tests performed
---------------
1. Friedman test on reading time across conditions (within-subjects)
2. Wilcoxon signed-rank post-hoc comparisons (C1 vs each AI condition)
3. Friedman test on comprehension accuracy
4. Wilcoxon signed-rank post-hoc for comprehension
5. Friedman test on scroll depth
6. Pearson correlation: confidence vs accuracy
7. Bonferroni correction applied to post-hoc comparisons

Output: output/dissertation/statistical_summary.png
"""

import sqlite3
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats as sp_stats
from itertools import combinations

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent.parent / "tos_research.db"

CONDITION_LABELS = {
    1: "C1 Plain Text",
    2: "C2 Scroll-Gated",
    3: "C3 Formatted",
    4: "C4 AI Summary",
    5: "C5 AI Enhanced",
    6: "C6 AI Hover",
}

# Map DB condition_group strings to numeric condition IDs
CONDITION_MAP = {
    "control": 1, "1": 1,
    "scroll-gate": 2, "2": 2,
    "formatted": 3, "3": 3,
    "ai-summary": 4, "4": 4,
    "ai-enhanced": 5, "5": 5,
    "ai-hover": 6, "6": 6,
}


def _get_paired_reading_times():
    """Get reading times as a participant × condition matrix."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name, s.condition_group, s.total_reading_time
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.total_reading_time IS NOT NULL
        ORDER BY u.name, s.condition_group
    """)
    rows = cur.fetchall()
    conn.close()

    user_data = {}
    for r in rows:
        cond_id = CONDITION_MAP.get(str(r["condition_group"]).lower())
        if cond_id is None:
            continue
        user_data.setdefault(r["name"], {})[cond_id] = (
            r["total_reading_time"]
        )

    # Only include participants with all 6 conditions
    complete = {u: d for u, d in user_data.items() if len(d) == 6}
    if not complete:
        return None, 0

    matrix = np.array([[d[c] for c in range(1, 7)]
                       for d in complete.values()])
    return matrix, len(complete)


def _get_paired_comprehension():
    """Get comprehension accuracy as participant × condition matrix."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT user_name, condition_scores
        FROM comprehension_tests
    """)
    rows = cur.fetchall()
    conn.close()

    user_data = {}
    for r in rows:
        scores = json.loads(r["condition_scores"]) if r["condition_scores"] else []
        d = {}
        for cs in scores:
            d[cs["condition"]] = cs.get("percentage", 0)
        if len(d) == 6:
            user_data[r["user_name"]] = d

    if not user_data:
        return None, 0

    matrix = np.array([[d[c] for c in range(1, 7)]
                       for d in user_data.values()])
    return matrix, len(user_data)


def _get_paired_scroll_depth():
    """Get max scroll depth as participant × condition matrix."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name, s.condition_group, s.max_scroll_depth
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.max_scroll_depth IS NOT NULL
        ORDER BY u.name, s.condition_group
    """)
    rows = cur.fetchall()
    conn.close()

    user_data = {}
    for r in rows:
        cond_id = CONDITION_MAP.get(str(r["condition_group"]).lower())
        if cond_id is None:
            continue
        user_data.setdefault(r["name"], {})[cond_id] = (
            float(r["max_scroll_depth"])
        )

    complete = {u: d for u, d in user_data.items() if len(d) == 6}
    if not complete:
        return None, 0

    matrix = np.array([[d[c] for c in range(1, 7)]
                       for d in complete.values()])
    return matrix, len(complete)


def _sig_marker(p):
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def _bonferroni(p, n_comparisons):
    return min(p * n_comparisons, 1.0)


def _run_tests():
    """Run all statistical tests, return list of result rows."""
    results = []

    # ── Reading time ─────────────────────────────────────────────────
    rt_matrix, n_rt = _get_paired_reading_times()
    if rt_matrix is not None and n_rt >= 3:
        stat, p = sp_stats.friedmanchisquare(*[rt_matrix[:, i] for i in range(6)])
        results.append(("Reading Time", "Friedman χ²", f"{stat:.2f}",
                        f"{p:.4f}", _sig_marker(p), f"N={n_rt}"))

        # Post-hoc: C1 vs C4, C5, C6 (AI conditions)
        n_comp = 3
        for c in [4, 5, 6]:
            try:
                stat_w, p_w = sp_stats.wilcoxon(rt_matrix[:, 0],
                                                 rt_matrix[:, c - 1])
                p_adj = _bonferroni(p_w, n_comp)
                results.append((
                    f"  C1 vs {CONDITION_LABELS[c]}",
                    "Wilcoxon W",
                    f"{stat_w:.2f}",
                    f"{p_adj:.4f}",
                    _sig_marker(p_adj),
                    "Bonferroni",
                ))
            except ValueError:
                pass

    # ── Comprehension ────────────────────────────────────────────────
    comp_matrix, n_comp_data = _get_paired_comprehension()
    if comp_matrix is not None and n_comp_data >= 3:
        stat, p = sp_stats.friedmanchisquare(
            *[comp_matrix[:, i] for i in range(6)])
        results.append(("Comprehension", "Friedman χ²", f"{stat:.2f}",
                        f"{p:.4f}", _sig_marker(p), f"N={n_comp_data}"))

        n_comp = 3
        for c in [4, 5, 6]:
            try:
                stat_w, p_w = sp_stats.wilcoxon(comp_matrix[:, 0],
                                                  comp_matrix[:, c - 1])
                p_adj = _bonferroni(p_w, n_comp)
                results.append((
                    f"  C1 vs {CONDITION_LABELS[c]}",
                    "Wilcoxon W",
                    f"{stat_w:.2f}",
                    f"{p_adj:.4f}",
                    _sig_marker(p_adj),
                    "Bonferroni",
                ))
            except ValueError:
                pass

    # ── Scroll depth ─────────────────────────────────────────────────
    scroll_matrix, n_scroll = _get_paired_scroll_depth()
    if scroll_matrix is not None and n_scroll >= 3:
        stat, p = sp_stats.friedmanchisquare(
            *[scroll_matrix[:, i] for i in range(6)])
        results.append(("Scroll Depth", "Friedman χ²", f"{stat:.2f}",
                        f"{p:.4f}", _sig_marker(p), f"N={n_scroll}"))

    # ── Confidence vs accuracy correlation ───────────────────────────
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT recognition_score, avg_confidence
        FROM comprehension_tests
        WHERE recognition_score IS NOT NULL AND avg_confidence IS NOT NULL
    """)
    rows = cur.fetchall()
    conn.close()

    if len(rows) >= 3:
        acc = [r["recognition_score"] for r in rows]
        conf = [r["avg_confidence"] for r in rows]
        r_val, p_val = sp_stats.pearsonr(conf, acc)
        results.append(("Confidence↔Accuracy", "Pearson r",
                        f"{r_val:.3f}", f"{p_val:.4f}",
                        _sig_marker(p_val), f"N={len(rows)}"))

    return results


def generate():
    results = _run_tests()

    if not results:
        print("[SKIP] Insufficient data for statistical tests.")
        return []

    # Print to console
    header = ("Measure", "Test", "Statistic", "p-value", "Sig.", "Note")
    col_widths = [max(len(r[i]) for r in results + [header])
                  for i in range(6)]
    fmt = "  ".join(f"{{:{w}}}" for w in col_widths)

    print("\n" + "=" * 70)
    print("STATISTICAL TESTS SUMMARY")
    print("=" * 70)
    print(fmt.format(*header))
    print("-" * sum(col_widths + [10]))
    for row in results:
        print(fmt.format(*row))
    print("=" * 70)
    print("* p<0.05  ** p<0.01  *** p<0.001  ns = not significant")
    print()

    # ── Render as table image ────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, max(3, 0.5 * len(results) + 2)))
    ax.axis("off")

    table = ax.table(
        cellText=[list(r) for r in results],
        colLabels=list(header),
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    # Style header row
    for j in range(len(header)):
        cell = table[0, j]
        cell.set_facecolor("#37474F")
        cell.set_text_props(color="white", fontweight="bold")

    # Highlight significant results
    for i, row in enumerate(results, start=1):
        sig = row[4]
        if sig != "ns":
            for j in range(len(header)):
                table[i, j].set_facecolor("#E8F5E9")

    ax.set_title("Statistical Tests Summary", fontsize=14,
                 fontweight="bold", pad=20)

    fig.text(
        0.5, 0.02,
        "Table: Summary of inferential statistics. "
        "Friedman tests assess overall differences across conditions; "
        "Wilcoxon signed-rank tests provide post-hoc comparisons between "
        "C1 (baseline) and AI conditions with Bonferroni correction. "
        "* p<0.05, ** p<0.01, *** p<0.001.",
        ha="center", fontsize=8.5, style="italic", wrap=True,
    )

    out = OUTPUT_DIR / "statistical_summary.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out}")
    return [out]


if __name__ == "__main__":
    generate()
