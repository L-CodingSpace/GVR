#!/usr/bin/env python3
"""Batch evaluation for abstract_reasoning (detailed mode)"""

from pathlib import Path
import subprocess
import json
import argparse

GVR_BASE = Path(__file__).parent.parent
VIDEO_BASE_DIR = Path(__file__).parent.parent / "0_generated_videos"
OUTPUT_BASE = Path(__file__).parent.parent.parent / "new_results_abstract"

MAIN_CAT = "abstract_reasoning"
FOLDER_NAME = "c1_abstract_reasoning"
SUB_CATS = ['2d_rule_extrapolation', '3d_rule_extrapolation', 'raven_matrix', 'symmetry']

TASK_IDS = {
    '2d_rule_extrapolation': ['01', '02', '03'],
    '3d_rule_extrapolation': ['01', '02', '03'],
    'raven_matrix': ['01', '02', '03'],
    'symmetry': ['random_01', 'random_02', 'random_03'],
}

def find_eval_py(sub_cat):
    eval_dir = GVR_BASE / FOLDER_NAME / sub_cat
    eval_py = eval_dir / f"{sub_cat}_eval.py"
    if eval_py.exists():
        return eval_py
    matches = list(eval_dir.glob("*eval.py"))
    if matches:
        for m in matches:
            if 'debug' not in m.name.lower():
                return m
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-model', required=True)
    args = parser.parse_args()
    
    video_model = args.video_model
    
    print("=" * 80)
    print(f"Batch evaluation for {MAIN_CAT} (detailed mode) - {video_model}")
    print(f"Output directory: {OUTPUT_BASE / video_model}")
    print("=" * 80)
    
    total_success = 0
    total_error = 0
    total_skipped = 0
    
    for i in range(5):
        subfolder = f"{video_model}_{i}"
        print(f"\n{'='*80}")
        print(f"Starting processing: {subfolder}")
        print(f"{'='*80}")
        
        subfolder_success = 0
        subfolder_error = 0
        subfolder_skipped = 0
        
        for sub_cat in SUB_CATS:
            eval_py = find_eval_py(sub_cat)
            if not eval_py:
                print(f"\n  ❌ Cannot find eval.py: {MAIN_CAT}/{sub_cat}")
                continue
            
            print(f"\n  Category: {MAIN_CAT}/{sub_cat}")
            
            for task_id in TASK_IDS[sub_cat]:
                CONFIG_DIR = VIDEO_BASE_DIR / video_model / "temp_eval_configs" / subfolder
                config_json = CONFIG_DIR / f"{MAIN_CAT}_{sub_cat}_eval.json"
                output_dir = OUTPUT_BASE / video_model / subfolder / MAIN_CAT / sub_cat
                output_file = output_dir / f"{task_id}_score.json"
                
                if not config_json.exists():
                    print(f"    [{task_id}] ❌ Configuration file does not exist")
                    subfolder_error += 1
                    continue
                
                if output_file.exists():
                    print(f"    [{task_id}] ⏭️  Already exists")
                    subfolder_skipped += 1
                    continue
                
                print(f"    [{task_id}] 🚀 Evaluating...", end=' ', flush=True)
                output_dir.mkdir(parents=True, exist_ok=True)
                
                result = subprocess.run(
                    ['python3', str(eval_py), '--task_id', task_id,
                     '--config', str(config_json), '--output', str(output_dir)],
                    cwd=eval_py.parent, capture_output=True, text=True, timeout=500
                )
                
                if result.returncode == 0 and output_file.exists():
                    with open(output_file, 'r') as f:
                        score = json.load(f).get('normalized_score', 'N/A')
                    print(f"✅ {score}")
                    subfolder_success += 1
                else:
                    print(f"❌ (Return code: {result.returncode})")
                    subfolder_error += 1
        
        print(f"\n{'-'*80}")
        print(f"{subfolder} completed: Success={subfolder_success}, Failed={subfolder_error}, Skipped={subfolder_skipped}")
        print(f"{'-'*80}")
        
        total_success += subfolder_success
        total_error += subfolder_error
        total_skipped += subfolder_skipped
    
    print(f"\n{'='*80}")
    print(f"{MAIN_CAT} evaluation completed")
    print(f"{'='*80}")
    print(f"Success: {total_success}")
    print(f"Failed: {total_error}")
    print(f"Skipped: {total_skipped}")
    print(f"Output directory: {OUTPUT_BASE / video_model}")

if __name__ == "__main__":
    main()

