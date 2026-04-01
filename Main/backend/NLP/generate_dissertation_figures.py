"""Generate all dissertation figures.

Usage:
    python generate_dissertation_figures.py        # Generate all figures
    python generate_dissertation_figures.py --list  # List available scripts

Similar to generate_visualisations.py but for publication-quality
dissertation figures rather than per-participant eye-tracking visualisations.
"""

import sys
import subprocess
from pathlib import Path


def main():
    script_dir = Path(__file__).parent / "dissertation_figures"

    scripts = [
        ("Architecture Diagram",        "architecture_diagram.py"),
        ("Coordinate Transformation",   "coordinate_transformation.py"),
        ("Experimental Design",         "experimental_design.py"),
        ("Reading Time Analysis",       "reading_time_analysis.py"),
        ("Scroll Depth Analysis",       "scroll_depth_analysis.py"),
        ("Comprehension Scores",        "comprehension_scores.py"),
        ("Preference Rankings",         "preference_rankings.py"),
        ("Statistical Tests",           "statistical_tests.py"),
        ("Completion Time",             "completion_time.py"),
        ("Engagement Metrics",          "engagement_metrics.py"),
        ("Scroll Behaviour",            "scroll_behaviour.py"),
        ("Study Procedure",             "study_procedure.py"),
    ]

    if "--list" in sys.argv:
        print("\nAvailable dissertation figure scripts:")
        print("-" * 50)
        for name, script in scripts:
            print(f"  {name:<30} {script}")
        print(f"\nOutput directory: output/dissertation/")
        return

    print(f"\n{'='*60}")
    print("GENERATING DISSERTATION FIGURES")
    print(f"{'='*60}")

    success = 0
    fail = 0

    for name, script in scripts:
        script_path = script_dir / script
        print(f"\n  Generating {name}...")
        print(f"  {'-'*50}")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            success += 1
        else:
            fail += 1
            print(f"  Warning: {script} exited with code {result.returncode}")

    print(f"\n{'='*60}")
    print(f"Done! {success} succeeded, {fail} failed.")
    print(f"{'='*60}")
    print(f"\nOutput directory: output/dissertation/")


if __name__ == "__main__":
    main()
