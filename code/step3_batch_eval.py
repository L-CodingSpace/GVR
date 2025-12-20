#!/usr/bin/env python3
"""
Step 3: Batch call eval.py for each subcategory
"""

from datasets import load_dataset
from pathlib import Path
import subprocess
import json
import argparse
from collections import defaultdict

GVR_BASE = Path(__file__).parent.parent
VIDEO_BASE_DIR = Path(__file__).parent.parent / "0_generated_videos"

CATEGORY_MAPPING = {
    'analogy_reasoning': 'analogy_resoning',
    'perceptual_reasoning': 'perceptural_reasoning',
    'planning_reasoning': 'planing_reasoning',
}

CAT_PREFIX_MAP = {
    'abstract_reasoning': 'c1',
    'analogy_resoning': 'c4',
    'perceptural_reasoning': 'c3',
    'planing_reasoning': 'c5',
    'spatial_reasoning': 'c6',
    'algorithmic_logical_reasoning': 'c2'
}

def find_eval_py(main_cat, sub_cat):
    """Find eval.py file"""
    folder_cat = CATEGORY_MAPPING.get(main_cat, main_cat)
    prefix = CAT_PREFIX_MAP.get(folder_cat, 'c1')
    eval_dir = GVR_BASE / f"{prefix}_{folder_cat}" / sub_cat
    
    patterns = [
        f"{sub_cat}_eval.py",
        "eval.py",
        f"{sub_cat.split('_')[0]}_eval.py",
    ]
    
    special_names = {
        '2d_rule_extrapolation': 'arc_eval.py',
        'auto_drive': 'autodrive_eval.py',
        'cross_word': 'crossword_eval.py',
    }
    
    if sub_cat in special_names:
        patterns.insert(0, special_names[sub_cat])
    
    for pattern in patterns:
        eval_py = eval_dir / pattern
        if eval_py.exists():
            return eval_py
    
    matches = list(eval_dir.glob("*eval.py"))
    if matches:
        for m in matches:
            if 'debug' not in m.name.lower():
                return m
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Batch run evaluation')
    parser.add_argument('--video-model', required=True, 
                       help='Video model name, e.g.: wan2.5, sora2, veo3.1, seedance-pro, seedance-lite')
    args = parser.parse_args()
    
    video_model = args.video_model
    
    print("=" * 80)
    print(f"Step 3: Batch run evaluation - {video_model}")
    print("=" * 80)
    
    print("Loading dataset...")
    ds = load_dataset('ciciciciliu/Gen-Vire_ds')['train']
    print(f"Dataset size: {len(ds)} items")
    
    # Group by (main_cat, sub_cat)
    samples_by_category = defaultdict(list)
    for sample in ds:
        key = (sample['main_category'], sample['sub_category'])
        samples_by_category[key].append(sample)
    
    print(f"Number of categories: {len(samples_by_category)}")
    
    total_success = 0
    total_error = 0
    total_skipped = 0
    
    # Outer loop: 5 subfolders
    for i in range(5):
        subfolder = f"{video_model}_{i}"
        
        print(f"\n{'='*80}")
        print(f"Starting processing: {subfolder}")
        print(f"{'='*80}")
        
        subfolder_success = 0
        subfolder_error = 0
        subfolder_skipped = 0
        
        # Middle loop: by category
        for (main_cat, sub_cat) in sorted(samples_by_category.keys()):
            samples = samples_by_category[(main_cat, sub_cat)]
            
            # Find eval.py (category level, find only once)
            eval_py = find_eval_py(main_cat, sub_cat)
            if not eval_py:
                continue
            
            print(f"\n  Category: {main_cat}/{sub_cat}")
            
            # Inner loop: by ID order
            for sample in sorted(samples, key=lambda x: x['id']):
                sample_id = sample['id']
                
                # Configuration file path
                CONFIG_DIR = VIDEO_BASE_DIR / video_model / "temp_eval_configs" / subfolder
                config_json = CONFIG_DIR / f"{main_cat}_{sub_cat}_eval.json"
                
                # Output path
                output_dir = VIDEO_BASE_DIR / video_model / subfolder / main_cat / sub_cat
                output_file = output_dir / f"{sample_id}_score.json"
                
                if not config_json.exists():
                    print(f"    [{sample_id}] ❌ Configuration file does not exist")
                    subfolder_error += 1
                    continue
                
                if output_file.exists():
                    print(f"    [{sample_id}] ⏭️  Already exists")
                    subfolder_skipped += 1
                    continue
                
                print(f"    [{sample_id}] 🚀 Evaluating...", end=' ', flush=True)
                
                output_dir.mkdir(parents=True, exist_ok=True)
                
                result = subprocess.run(
                    [
                        'python3', str(eval_py),
                        '--task_id', sample_id,
                        '--config', str(config_json),
                        '--output', str(output_dir),
                    ],
                    cwd=eval_py.parent,
                    capture_output=True,
                    text=True,
                    timeout=500
                )
                
                if result.returncode == 0 and output_file.exists():
                    with open(output_file, 'r') as f:
                        score_data = json.load(f)
                        score = score_data.get('normalized_score', 'N/A')
                    print(f"✅ {score}")
                    subfolder_success += 1
                else:
                    print(f"❌ (Return code: {result.returncode})")
                    if result.stderr:
                        stderr_lines = [l for l in result.stderr.split('\n') if l.strip() and 'Warning' not in l]
                        if stderr_lines:
                            print(f"         Error: {stderr_lines[-1][:100]}")
                    subfolder_error += 1
        
        # Print subfolder statistics
        print(f"\n{'-'*80}")
        print(f"{subfolder} completed: Success={subfolder_success}, Failed={subfolder_error}, Skipped={subfolder_skipped}")
        print(f"{'-'*80}")
        
        # Add to total statistics
        total_success += subfolder_success
        total_error += subfolder_error
        total_skipped += subfolder_skipped
    
    print(f"\n{'='*80}")
    print("Evaluation completed")
    print(f"{'='*80}")
    print(f"Success: {total_success}")
    print(f"Failed: {total_error}")
    print(f"Skipped: {total_skipped}")
    print(f"Output directory: {VIDEO_BASE_DIR / video_model}")

if __name__ == "__main__":
    main()

# python step3_batch_eval.py --video-model wan2.5