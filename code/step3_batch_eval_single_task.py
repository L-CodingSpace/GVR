#!/usr/bin/env python3
"""Batch evaluation for single subcategory (detailed mode)"""

from datasets import load_dataset
from pathlib import Path
import subprocess
import json
import argparse

GVR_BASE = Path(__file__).parent.parent
VIDEO_BASE_DIR = Path(__file__).parent.parent / "0_generated_videos"
OUTPUT_BASE = Path(__file__).parent.parent.parent / "new_results_single_task"

CATEGORY_MAPPING = {
    'abstract_reasoning': 'c1_abstract_reasoning',
    'algorithmic_logical_reasoning': 'c2_algorithmic_logical_reasoning',
    'perceptual_reasoning': 'c3_perceptural_reasoning',
    'analogy_reasoning': 'c4_analogy_resoning',
    'planning_reasoning': 'c5_planing_reasoning',
    'spatial_reasoning': 'c6_spatial_reasoning',
}

def find_eval_py(main_cat, sub_cat):
    folder_name = CATEGORY_MAPPING.get(main_cat, main_cat)
    eval_dir = GVR_BASE / folder_name / sub_cat
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
    parser.add_argument('--main-category', required=True)
    parser.add_argument('--sub-category', required=True)
    args = parser.parse_args()
    
    video_model = args.video_model
    main_cat = args.main_category
    sub_cat = args.sub_category
    
    print("=" * 80)
    print(f"Batch evaluation for single subcategory (detailed mode) - {video_model}")
    print(f"Category: {main_cat}/{sub_cat}")
    print(f"Output directory: {OUTPUT_BASE / video_model / main_cat / sub_cat}")
    print("=" * 80)
    
    print("Loading dataset...")
    ds = load_dataset('ciciciciliu/Gen-Vire_ds')['train']
    
    samples = [s for s in ds 
               if s['main_category'] == main_cat 
               and s['sub_category'] == sub_cat]
    
    print(f"Number of samples: {len(samples)}")
    
    eval_py = find_eval_py(main_cat, sub_cat)
    if not eval_py:
        print(f"❌ Cannot find eval.py: {main_cat}/{sub_cat}")
        return
    
    print(f"Evaluation script: {eval_py}\n")
    
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
        
        for sample in sorted(samples, key=lambda x: x['id']):
            sample_id = sample['id']
            
            CONFIG_DIR = VIDEO_BASE_DIR / video_model / "temp_eval_configs" / subfolder
            config_json = CONFIG_DIR / f"{main_cat}_{sub_cat}_eval.json"
            output_dir = OUTPUT_BASE / video_model / subfolder / main_cat / sub_cat
            output_file = output_dir / f"{sample_id}_score.json"
            
            if not config_json.exists():
                print(f"  [{sample_id}] ❌ Configuration file does not exist")
                subfolder_error += 1
                continue
            
            if output_file.exists():
                print(f"  [{sample_id}] ⏭️  Already exists")
                subfolder_skipped += 1
                continue
            
            print(f"  [{sample_id}] 🚀 Evaluating...", end=' ', flush=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['python3', str(eval_py), '--task_id', sample_id,
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
    print(f"{main_cat}/{sub_cat} evaluation completed")
    print(f"{'='*80}")
    print(f"Success: {total_success}")
    print(f"Failed: {total_error}")
    print(f"Skipped: {total_skipped}")
    print(f"Output directory: {OUTPUT_BASE / video_model}")

if __name__ == "__main__":
    main()

