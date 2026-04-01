"""Scroll Behaviour Breakdown for Dissertation.

Generates a stacked bar chart showing the proportion of
quick-scroll / thorough-read / partial-read per condition.

Figures produced
----------------
- scroll_behaviour_breakdown.png – Stacked proportions per condition
- completion_rate.png            – % of participants reaching 100% scroll

Output: output/dissertation/
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent.parent / "tos_research.db"

CONDITION_LABELS = {
    "control": "C1\nPlain Text",
    "scroll-gate": "C2\nScroll-Gated",
    "formatted": "C3\nFormatted",
    "ai-summary": "C4\nAI Summary",
    "ai-enhanced": "C5\nAI Enhanced",
    "ai-hover": "C6\nAI Hover",
}
CONDITION_ORDER = {
    "control": 1, "scroll-gate": 2, "formatted": 3,
    "ai-summary": 4, "ai-enhanced": 5, "ai-hover": 6,
}
CONDITION_COLOURS = {
    "control": "#78909C",
    "scroll-gate": "#5C6BC0",
    "formatted": "#26A69A",
    "ai-summary": "#FFA726",
    "ai-enhanced": "#EF5350",
    "ai-hover": "#AB47BC",
}

BEHAVIOUR_COLOURS = {
    "quick-scroll": "#EF5350",
    "thorough-read": "#26A69A",
    "partial-read": "#FFA726",
}
BEHAVIOUR_LABELS = {
    "quick-scroll": "Quick Scroll",
    "thorough-read": "Thorough Read",
    "partial-read": "Partial Read",
}


def _load_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT s.condition_group, s.scroll_behavior, s.did_read_complete
        FROM sessions s
        WHERE s.scroll_behavior IS NOT NULL
    """)
    rows = cur.fetchall()
    conn.close()

    behaviour = {}   # condition -> {behaviour -> count}
    completion = {}   # condition -> {True: n, False: n}
    for r in rows:
        cond = str(r["condition_group"])
        beh = r["scroll_behavior"]
        done = bool(r["did_read_complete"])

        behaviour.setdefault(cond, {})
        behaviour[cond][beh] = behaviour[cond].get(beh, 0) + 1

        completion.setdefault(cond, {"done": 0, "total": 0})
        completion[cond]["total"] += 1
        if done:
            completion[cond]["done"] += 1

    return behaviour, completion


def generate():
    behaviour, completion = _load_data()
    if not behaviour:
        print("[SKIP] No scroll-behaviour data in database.")
        return []

    outputs = []
    conditions = sorted(behaviour.keys(),
                        key=lambda c: CONDITION_ORDER.get(c, 99))
    labels = [CONDITION_LABELS.get(c, c) for c in conditions]

    beh_types = ["thorough-read", "partial-read", "quick-scroll"]

    # ── 1. Stacked bar – scroll behaviour proportions ────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    bottoms = np.zeros(len(conditions))

    for btype in beh_types:
        counts = []
        for c in conditions:
            total = sum(behaviour[c].values())
            counts.append(behaviour[c].get(btype, 0) / total * 100
                          if total > 0 else 0)
        ax.bar(x, counts, bottom=bottoms, width=0.55,
               color=BEHAVIOUR_COLOURS[btype], edgecolor="white",
               linewidth=1.2, label=BEHAVIOUR_LABELS[btype])
        bottoms += np.array(counts)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Proportion (%)", fontsize=11)
    ax.set_title("Scroll Behaviour Breakdown per Condition", fontsize=13,
                 fontweight="bold")
    ax.set_ylim(0, 105)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        "Figure: Proportion of scroll behaviour categories per condition. "
        "Quick-scroll = > 500 WPM (not reading); Thorough-read = 150–300 WPM "
        "and reached bottom; Partial-read = all other sessions.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out1 = OUTPUT_DIR / "scroll_behaviour_breakdown.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Completion rate (% reaching 100% scroll) ──────────────────
    conds_c = sorted(completion.keys(),
                     key=lambda c: CONDITION_ORDER.get(c, 99))
    labels_c = [CONDITION_LABELS.get(c, c) for c in conds_c]
    colours_c = [CONDITION_COLOURS.get(c, "#999") for c in conds_c]
    rates = [completion[c]["done"] / completion[c]["total"] * 100
             if completion[c]["total"] > 0 else 0 for c in conds_c]

    fig, ax = plt.subplots(figsize=(10, 6))
    xc = np.arange(len(conds_c))
    bars = ax.bar(xc, rates, width=0.55, color=colours_c, alpha=0.8,
                  edgecolor="white", linewidth=1.2)

    for i, r in enumerate(rates):
        ax.text(xc[i], r + 1, f"{r:.0f}%",
                ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_xticks(xc)
    ax.set_xticklabels(labels_c)
    ax.set_ylabel("Completion Rate (%)", fontsize=11)
    ax.set_title("Document Completion Rate per Condition", fontsize=13,
                 fontweight="bold")
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        "Figure: Percentage of participants who scrolled to ≥ 99% of "
        "the document per condition. Completion defined as reaching "
        "the bottom of the ToS document.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out2 = OUTPUT_DIR / "completion_rate.png"
    fig.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out2}")
    outputs.append(out2)

    return outputs


if __name__ == "__main__":
    generate()
