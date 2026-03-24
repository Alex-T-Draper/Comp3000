"""Generate all visualizations for a user (or all users).

Usage:
    python generate_visualizations.py              # All users
    python generate_visualizations.py {user}       # Specific user
"""

import sys
import subprocess
from pathlib import Path

def main():
    # Get username from command line argument
    user_filter = sys.argv[1] if len(sys.argv) > 1 else None
    
    if user_filter:
        print(f"\n{'='*60}")
        print(f"Generating visualizations for user: {user_filter}")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("Generating visualizations for all users")
        print('='*60)
    
    # List of visualization scripts to run
    scripts = [
        "visualisations/generate_heatmap.py",
        "visualisations/generate_scanpath.py",
        "visualisations/generate_fixation_bubbles.py",
        "visualisations/generate_aoi.py"
    ]
    
    # Run each script
    for script in scripts:
        script_name = Path(script).stem.replace('generate_', '').replace('_', ' ').title()
        print(f"\nGenerating {script_name}...")
        print('-'*60)
        
        # Build command
        cmd = [sys.executable, script]
        if user_filter:
            cmd.append(user_filter)
        
        # Run the script
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"Warning: {script} failed with code {result.returncode}")
    
    print(f"\n{'='*60}")
    print("All visualizations complete!")
    print('='*60)
    
    if user_filter:
        print(f"\nCheck the output folders for files containing: {user_filter}")
    
    print("\nOutput directories:")
    print("  - output/heatmaps/")
    print("  - output/scanpaths/")
    print("  - output/bubbles/")
    print("  - output/aoi/")


if __name__ == "__main__":
    main()