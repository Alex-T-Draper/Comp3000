"""Comprehension Test Score Figures for Dissertation.

Generates charts from the comprehension_tests table:
- Per-condition recognition accuracy (bar chart)
- Average confidence ratings (bar chart)
- Recognition vs Confidence scatter / correlation

Output: output/dissertation/
"""

import sqlite3
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats as sp_stats

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent.parent / "tos_research.db"

CONDITION_LABELS = {
    1: "C1\nPlain Text",
    2: "C2\nScroll-Gated",
    3: "C3\nFormatted",
    4: "C4\nAI Summary",
    5: "C5\nAI Enhanced",
    6: "C6\nAI Hover",
}

CONDITION_SHORT = {
    1: "C1 Plain",
    2: "C2 Scroll",
    3: "C3 Format",
    4: "C4 Summary",
    5: "C5 Enhanced",
    6: "C6 Hover",
}

CONDITION_COLOURS = {
    1: "#78909C",
    2: "#5C6BC0",
    3: "#26A69A",
    4: "#FFA726",
    5: "#EF5350",
    6: "#AB47BC",
}


def _load_comprehension_data():
    """Load comprehension test results with per-condition breakdown."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT user_name, recognition_score, avg_confidence,
               condition_scores, confidence_answers
        FROM comprehension_tests
        ORDER BY user_name
    """)
    rows = cur.fetchall()
    conn.close()

    participants = []
    anon_map = {}
    for r in rows:
        uname = r["user_name"]
        if uname not in anon_map:
            anon_map[uname] = f"P{len(anon_map) + 1:02d}"

        cond_scores = json.loads(r["condition_scores"]) if r["condition_scores"] else []
        conf_answers = json.loads(r["confidence_answers"]) if r["confidence_answers"] else []

        participants.append({
            "pid": anon_map[uname],
            "recognition_score": r["recognition_score"],
            "avg_confidence": r["avg_confidence"],
            "condition_scores": cond_scores,
            "confidence_answers": conf_answers,
        })

    return participants, anon_map


def _add_significance_bracket(ax, x1, x2, y, p_value, h=0.02):
    """Draw a significance bracket between two bars."""
    if p_value >= 0.05:
        return
    marker = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.2, c="black")
    ax.text((x1 + x2) / 2, y + h, marker, ha="center", va="bottom",
            fontsize=10, fontweight="bold")


def generate():
    participants, anon_map = _load_comprehension_data()
    n = len(anon_map)

    if not participants:
        print("[SKIP] No comprehension test data in database.")
        return []

    outputs = []

    # ── Build per-condition accuracy arrays ──────────────────────────
    cond_pcts = {c: [] for c in range(1, 7)}
    for p in participants:
        for cs in p["condition_scores"]:
            cond = cs.get("condition")
            pct = cs.get("percentage", 0)
            if cond in cond_pcts:
                cond_pcts[cond].append(pct)

    conditions = sorted(cond_pcts.keys())
    labels = [CONDITION_LABELS[c] for c in conditions]
    colours = [CONDITION_COLOURS[c] for c in conditions]

    # ── 1. Per-condition recognition accuracy ────────────────────────
    means = [np.mean(cond_pcts[c]) if cond_pcts[c] else 0 for c in conditions]
    sems = [sp_stats.sem(cond_pcts[c]) if len(cond_pcts[c]) > 1 else 0
            for c in conditions]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    bars = ax.bar(x, means, yerr=sems, capsize=5, width=0.55,
                  color=colours, alpha=0.85, edgecolor="white", linewidth=1.2,
                  error_kw={"lw": 1.5})
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Recognition Accuracy (%)", fontsize=11)
    ax.set_ylim(0, 110)
    ax.axhline(33.3, color="#ccc", ls="--", lw=0.8, label="Chance level (33%)")
    ax.set_title("Comprehension Test Accuracy per Condition",
                 fontsize=13, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # Overlay individual points
    rng = np.random.default_rng(42)
    for i, c in enumerate(conditions):
        pts = cond_pcts[c]
        if pts:
            jitter = rng.uniform(-0.15, 0.15, len(pts))
            ax.scatter(x[i] + jitter, pts, color="black", alpha=0.35,
                       s=18, zorder=5)

    # Statistical significance between C1 (baseline) and AI conditions
    max_y = max(m + s for m, s in zip(means, sems)) + 5
    for i, c in enumerate(conditions):
        if c == 1 or not cond_pcts[1] or not cond_pcts[c]:
            continue
        _, p = sp_stats.mannwhitneyu(cond_pcts[1], cond_pcts[c],
                                     alternative="two-sided")
        _add_significance_bracket(ax, 0, i, max_y + (i - 1) * 4, p, h=1.5)

    fig.text(
        0.5, -0.03,
        f"Figure: Comprehension test accuracy per condition (N={n}). "
        "Error bars show ± SE. Black dots are individual participants. "
        "Dashed line = chance. * p<0.05, ** p<0.01, *** p<0.001 "
        "(Mann–Whitney U vs. C1).",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out1 = OUTPUT_DIR / "comprehension_accuracy.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Average confidence ratings ────────────────────────────────
    conf_values = [p["avg_confidence"] for p in participants
                   if p["avg_confidence"] is not None]

    if conf_values:
        # Aggregate per-question confidence across participants
        q_ratings = {}
        for p in participants:
            for ca in p["confidence_answers"]:
                qid = ca.get("questionId", ca.get("question", ""))
                rating = ca.get("rating")
                if rating is not None:
                    q_ratings.setdefault(qid, []).append(rating)

        if q_ratings:
            q_ids = sorted(q_ratings.keys())
            q_means = [np.mean(q_ratings[q]) for q in q_ids]
            q_sems = [sp_stats.sem(q_ratings[q]) if len(q_ratings[q]) > 1
                      else 0 for q in q_ids]
            q_labels = [f"Q{i+1}" for i in range(len(q_ids))]

            fig, ax = plt.subplots(figsize=(8, 5))
            x = np.arange(len(q_ids))
            ax.bar(x, q_means, yerr=q_sems, capsize=4, width=0.5,
                   color="#42A5F5", alpha=0.85, edgecolor="white",
                   error_kw={"lw": 1.5})
            ax.set_xticks(x)
            ax.set_xticklabels(q_labels)
            ax.set_ylabel("Mean Confidence Rating (1–5)", fontsize=11)
            ax.set_ylim(0, 5.5)
            ax.set_title("Self-Reported Confidence in ToS Understanding",
                         fontsize=13, fontweight="bold")
            ax.grid(axis="y", alpha=0.3)

            fig.text(
                0.5, -0.03,
                f"Figure: Mean self-reported confidence per question (N={n}). "
                "Scale: 1 = not confident, 5 = very confident. "
                "Error bars show ± SE.",
                ha="center", fontsize=9, style="italic", wrap=True,
            )
            out2 = OUTPUT_DIR / "confidence_ratings.png"
            fig.savefig(out2, dpi=300, bbox_inches="tight")
            plt.close(fig)
            print(f"[OK] {out2}")
            outputs.append(out2)

    # ── 3. Recognition score vs confidence scatter ───────────────────
    rec_scores = [p["recognition_score"] for p in participants
                  if p["recognition_score"] is not None
                  and p["avg_confidence"] is not None]
    conf_scores = [p["avg_confidence"] for p in participants
                   if p["recognition_score"] is not None
                   and p["avg_confidence"] is not None]

    if len(rec_scores) >= 3:
        fig, ax = plt.subplots(figsize=(7, 6))
        ax.scatter(conf_scores, rec_scores, c="#1565C0", s=50, alpha=0.7,
                   edgecolors="white", linewidth=0.5, zorder=5)

        # Trend line
        r, p_val = sp_stats.pearsonr(conf_scores, rec_scores)
        z = np.polyfit(conf_scores, rec_scores, 1)
        xline = np.linspace(min(conf_scores) - 0.2,
                            max(conf_scores) + 0.2, 50)
        ax.plot(xline, np.polyval(z, xline), "--", color="#E53935", lw=1.5,
                label=f"r = {r:.2f}, p = {p_val:.3f}")

        ax.set_xlabel("Average Confidence Rating (1–5)", fontsize=11)
        ax.set_ylabel("Recognition Accuracy (%)", fontsize=11)
        ax.set_title("Confidence vs. Comprehension Accuracy", fontsize=13,
                     fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)

        sig = ""
        if p_val < 0.001:
            sig = "***"
        elif p_val < 0.01:
            sig = "**"
        elif p_val < 0.05:
            sig = "*"

        fig.text(
            0.5, -0.03,
            f"Figure: Relationship between self-reported confidence and "
            f"recognition accuracy (N={len(rec_scores)}). "
            f"Pearson r = {r:.2f}{sig}. "
            "Axes: x = confidence (1–5), y = accuracy (%).",
            ha="center", fontsize=9, style="italic", wrap=True,
        )
        out3 = OUTPUT_DIR / "confidence_vs_accuracy.png"
        fig.savefig(out3, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"[OK] {out3}")
        outputs.append(out3)

    return outputs


if __name__ == "__main__":
    generate()
