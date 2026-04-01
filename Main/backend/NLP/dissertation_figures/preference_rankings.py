"""Preference Ranking Figures for Dissertation.

Generates charts from post-study preference/ranking data.
This script provides a framework that works with both:
  a) database-stored preferences (if available), or
  b) manually entered ranking data from the post-study questionnaire.

Update MANUAL_RANKINGS below if data is not yet in the database.

Output: output/dissertation/
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats as sp_stats

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "dissertation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITION_LABELS = {
    1: "C1 Plain Text",
    2: "C2 Scroll-Gated",
    3: "C3 Formatted",
    4: "C4 AI Summary",
    5: "C5 AI Enhanced",
    6: "C6 AI Hover",
}

CONDITION_COLOURS = {
    1: "#78909C",
    2: "#5C6BC0",
    3: "#26A69A",
    4: "#FFA726",
    5: "#EF5350",
    6: "#AB47BC",
}

# ── Manual ranking data ─────────────────────────────────────────────
# Each row = one participant's ranking (1 = most preferred, 6 = least).
# Columns correspond to conditions C1–C6.
# Replace with actual data from post-study questionnaires.
MANUAL_RANKINGS = np.array([
    # C1  C2  C3  C4  C5  C6     ← condition
    #  Participant rankings (1=best, 6=worst)
    # Uncomment and fill when data is collected:
    # [5, 6, 3, 2, 1, 4],  # P01
    # [6, 5, 4, 1, 2, 3],  # P02
    # ...
]).reshape(-1, 6) if False else None  # Set to True when data is entered


def _try_load_from_db():
    """Attempt to load preference data from the database."""
    import sqlite3
    db_path = Path(__file__).parent.parent / "tos_research.db"
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check if a preferences table exists
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='preference_rankings'
    """)
    if not cur.fetchone():
        conn.close()
        return None

    cur.execute("SELECT * FROM preference_rankings ORDER BY user_name")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    rankings = []
    for r in rows:
        rankings.append([r[f"c{c}_rank"] for c in range(1, 7)])
    return np.array(rankings)


def generate():
    rankings = _try_load_from_db()
    if rankings is None:
        rankings = MANUAL_RANKINGS
    if rankings is None or len(rankings) == 0:
        print("[SKIP] No preference ranking data available.")
        print("       Edit MANUAL_RANKINGS in preference_rankings.py")
        print("       or create a preference_rankings table in the database.")
        return []

    n = len(rankings)
    conditions = list(range(1, 7))
    labels = [CONDITION_LABELS[c] for c in conditions]
    colours = [CONDITION_COLOURS[c] for c in conditions]
    outputs = []

    # ── 1. Mean rank bar chart (lower = more preferred) ──────────────
    mean_ranks = rankings.mean(axis=0)
    sem_ranks = sp_stats.sem(rankings, axis=0) if n > 1 else np.zeros(6)

    # Sort by mean rank (best first)
    order = np.argsort(mean_ranks)
    sorted_labels = [labels[i] for i in order]
    sorted_means = mean_ranks[order]
    sorted_sems = sem_ranks[order]
    sorted_colours = [colours[i] for i in order]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(6)
    ax.barh(x, sorted_means, xerr=sorted_sems, capsize=4, height=0.55,
            color=sorted_colours, alpha=0.85, edgecolor="white",
            error_kw={"lw": 1.5})
    ax.set_yticks(x)
    ax.set_yticklabels(sorted_labels)
    ax.set_xlabel("Mean Preference Rank (1 = most preferred)", fontsize=11)
    ax.set_title("Participant Preference Rankings", fontsize=13,
                 fontweight="bold")
    ax.set_xlim(0, 7)
    ax.invert_xaxis()
    ax.grid(axis="x", alpha=0.3)

    fig.text(
        0.5, -0.03,
        f"Figure: Mean preference rank across conditions (N={n}). "
        "Lower rank indicates higher preference (1 = most preferred, "
        "6 = least preferred). Error bars show ± SE.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out1 = OUTPUT_DIR / "preference_rankings.png"
    fig.savefig(out1, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out1}")
    outputs.append(out1)

    # ── 2. Rank distribution heatmap ─────────────────────────────────
    # Rows = conditions, columns = ranks 1-6, cell = count
    rank_matrix = np.zeros((6, 6), dtype=int)
    for row in rankings:
        for cond_idx, rank_val in enumerate(row):
            rank_matrix[cond_idx, int(rank_val) - 1] += 1

    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(rank_matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"Rank {i+1}" for i in range(6)])
    ax.set_yticks(range(6))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Rank Position", fontsize=11)
    ax.set_title("Preference Rank Distribution", fontsize=13,
                 fontweight="bold")

    # Annotate cells
    for i in range(6):
        for j in range(6):
            val = rank_matrix[i, j]
            colour = "white" if val > n / 3 else "black"
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=11, fontweight="bold", color=colour)

    fig.colorbar(im, ax=ax, label="Count", shrink=0.8)

    fig.text(
        0.5, -0.03,
        f"Figure: Distribution of preference ranks (N={n}). "
        "Each cell shows how many participants assigned that rank "
        "to the condition. Darker = more frequent.",
        ha="center", fontsize=9, style="italic", wrap=True,
    )
    out2 = OUTPUT_DIR / "preference_heatmap.png"
    fig.savefig(out2, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {out2}")
    outputs.append(out2)

    # ── 3. Friedman test annotation ──────────────────────────────────
    if n >= 3:
        stat, p = sp_stats.friedmanchisquare(*[rankings[:, i]
                                                for i in range(6)])
        print(f"[STAT] Friedman χ²={stat:.2f}, p={p:.4f}")

    return outputs


if __name__ == "__main__":
    generate()
