"""Scroll Depth Analysis Figures for Dissertation.

Generates visualisations of scrolling behaviour across conditions:
- max scroll depth per condition (boxplot)
- scroll-up count per condition (bar chart)
- scroll depth over time (line charts)

Output: output/dissertation/
"""

import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats as sp_stats

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(__file__).parent.parent / "tos_research.db"

CONDITION_LABELS = {
    "1": "C1\nPlain Text",
    "2": "C2\nScroll-Gated",
    "3": "C3\nFormatted",
    "4": "C4\nAI Summary",
    "5": "C5\nAI Enhanced",
    "6": "C6\nAI Hover",
    "control": "C1\nPlain Text",
    "scroll-gate": "C2\nScroll-Gated",
    "formatted": "C3\nFormatted",
    "ai-summary": "C4\nAI Summary",
    "ai-enhanced": "C5\nAI Enhanced",
    "ai-hover": "C6\nAI Hover",
}

CONDITION_COLOURS = {
    "1": "#78909C",
    "2": "#5C6BC0",
    "3": "#26A69A",
    "4": "#FFA726",
    "5": "#EF5350",
    "6": "#AB47BC",
    "control": "#78909C",
    "scroll-gate": "#5C6BC0",
    "formatted": "#26A69A",
    "ai-summary": "#FFA726",
    "ai-enhanced": "#EF5350",
    "ai-hover": "#AB47BC",
}

CONDITION_ORDER = {
    "1": 1, "control": 1,
    "2": 2, "scroll-gate": 2,
    "3": 3, "formatted": 3,
    "4": 4, "ai-summary": 4,
    "5": 5, "ai-enhanced": 5,
    "6": 6, "ai-hover": 6,
}


def _anonymise(user_name: str, mapping: dict) -> str:
    if user_name not in mapping:
        mapping[user_name] = f"P{len(mapping) + 1:02d}"
    return mapping[user_name]


def _load_scroll_data():
    """Load max_scroll_depth & scroll_up_count per session."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT u.name AS user_name,
               s.condition_group,
               s.max_scroll_depth,
               s.scroll_up_count,
               s.re_read_sections
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.max_scroll_depth IS NOT NULL
        ORDER BY s.condition_group
    """)
    rows = cur.fetchall()
    conn.close()

    anon = {}
    depth_data = {}   # cond -> list of floats (0-100 %)
    scroll_up = {}    # cond -> list of ints
    reread = {}       # cond -> list of ints

    for r in rows:
        cond = str(r["condition_group"])
        _anonymise(r["user_name"], anon)

        depth_data.setdefault(cond, []).append(
            float(r["max_scroll_depth"] or 0)
        )
        scroll_up.setdefault(cond, []).append(int(r["scroll_up_count"] or 0))
        reread.setdefault(cond, []).append(int(r["re_read_sections"] or 0))

    return depth_data, scroll_up, reread, anon


def _load_scroll_events():
    """Load timestamped scroll events for scroll-over-time curves."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT se.session_id, se.timestamp, se.scroll_depth,
               s.condition_group
        FROM scroll_events se
        JOIN sessions s ON se.session_id = s.session_id
        ORDER BY se.session_id, se.timestamp
    """)
    rows = cur.fetchall()
    conn.close()

    events = {}  # cond -> list of (timestamps[], depths[])
    current_sid = None
    ts_buf, depth_buf, cond_buf = [], [], None

    for r in rows:
        sid = r["session_id"]
        if sid != current_sid:
            if current_sid and ts_buf:
                events.setdefault(cond_buf, []).append((ts_buf, depth_buf))
            ts_buf, depth_buf = [], []
            current_sid = sid
            cond_buf = str(r["condition_group"])
        ts_buf.append(r["timestamp"])
        depth_buf.append(float(r["scroll_depth"]))

    if current_sid and ts_buf:
        events.setdefault(cond_buf, []).append((ts_buf, depth_buf))

    return events


def generate():
    depth_data, scroll_up, reread, anon = _load_scroll_data()
    n = len(anon)

    if not depth_data:
        print("[SKIP] No scroll data in database.")
        return []

    conditions = sorted(depth_data.keys(), key=lambda c: CONDITION_ORDER.get(c, 99))
    labels = [CONDITION_LABELS.get(c, c) for c in conditions]
    colours = [CONDITION_COLOURS.get(c, "#999") for c in conditions]
    outputs = []

    # ── 1. Max scroll depth boxplot ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
    vals = [depth_data[c] for c in conditions]
    bp = ax.boxplot(vals, labels=labels, patch_artist=True, widths=0.5)
    for patch, col in zip(bp["boxes"], colours):
        patch.set_facecolor(col)
        patch.set_alpha(0.75)
    ax.set_ylabel("Max Scroll Depth (%)", fontsize=11)
    ax.set_title("Maximum Scroll Depth per Condition", fontsize=13,
                 fontweight="bold")
    ax.set_ylim(0, 105)
    ax.axhline(100, color="#aaa", ls="--", lw=0.8, label="Document end")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Maximum scroll depth reached per condition (N={n}). "
        "100 % indicates the participant scrolled to the bottom of the "
        "document. Axes: x = condition, y = scroll depth percentage.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out1 = OUTPUT_DIR / "scroll_depth_boxplot.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Scroll-up count bar chart ─────────────────────────────────
    means = [np.mean(scroll_up[c]) for c in conditions]
    sems = [sp_stats.sem(scroll_up[c]) if len(scroll_up[c]) > 1 else 0
            for c in conditions]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(conditions))
    ax.bar(x, means, yerr=sems, capsize=5, width=0.55,
           color=colours, alpha=0.8, edgecolor="white", linewidth=1.2,
           error_kw={"lw": 1.5})
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Scroll-Up Events (count)", fontsize=11)
    ax.set_title("Mean Scroll-Up Count per Condition (± SE)", fontsize=13,
                 fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Mean number of scroll-up events per condition (N={n}). "
        "Higher counts may indicate re-reading behaviour. "
        "Error bars show standard error of the mean.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out2 = OUTPUT_DIR / "scroll_up_count.png"
    fig.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out2}")
    outputs.append(out2)

    # ── 3. Scroll depth over time (aggregate per condition) ──────────
    events = _load_scroll_events()
    if events:
        fig, ax = plt.subplots(figsize=(12, 6))
        for c in conditions:
            if c not in events:
                continue
            # Normalise each session's timestamps to 0-1 range, then average
            all_norm_depths = []
            n_bins = 100
            for ts_list, depth_list in events[c]:
                if len(ts_list) < 2:
                    continue
                depths = np.array(depth_list)
                # bin into n_bins buckets (normalised time)
                indices = np.linspace(0, len(depths) - 1, n_bins).astype(int)
                all_norm_depths.append(depths[indices])

            if all_norm_depths:
                arr = np.array(all_norm_depths)
                mean_d = arr.mean(axis=0)
                sem_d = sp_stats.sem(arr, axis=0) if arr.shape[0] > 1 else np.zeros(n_bins)
                t = np.linspace(0, 100, n_bins)
                col = CONDITION_COLOURS.get(c, "#999")
                ax.plot(t, mean_d, color=col, lw=2,
                        label=CONDITION_LABELS.get(c, c).replace("\n", " "))
                ax.fill_between(t, mean_d - sem_d, mean_d + sem_d,
                                color=col, alpha=0.15)

        ax.set_xlabel("Normalised Reading Progress (%)", fontsize=11)
        ax.set_ylabel("Scroll Depth (%)", fontsize=11)
        ax.set_title("Scroll Depth Over Normalised Reading Time",
                     fontsize=13, fontweight="bold")
        ax.legend(fontsize=8, ncol=2)
        ax.grid(alpha=0.3)

        fig.text(
            0.5, -0.03,
            f"Figure: Aggregate scroll depth over normalised reading progress "
            f"(N={n}). Shaded regions show ± SE. "
            "Axes: x = % of reading session elapsed, y = scroll depth %.",
            ha="center", fontsize=9, style="italic", wrap=True,
        )
        out3 = OUTPUT_DIR / "scroll_depth_over_time.png"
        fig.savefig(out3, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"[OK] {out3}")
        outputs.append(out3)

    return outputs


if __name__ == "__main__":
    generate()
