#!/usr/bin/env python3
"""
Step 2: Generate updated configuration JSON for each subcategory
"""

from datasets import load_dataset,load_from_disk
import json
from pathlib import Path
from collections import defaultdict
import argparse

GVR_BASE = Path(__file__).parent.parent
VIDEO_BASE_DIR = Path(__file__).parent.parent / "0_generated_videos"

# Category name mapping (dataset -> folder)
CATEGORY_MAPPING = {
    'analogy_reasoning': 'c4_analogy_resoning',
    'perceptual_reasoning': 'c3_perceptural_reasoning',
    'planning_reasoning': 'c5_planing_reasoning',
    'spatial_reasoning': 'c6_spatial_reasoning',
    'algorithmic_logical_reasoning': 'c2_algorithmic_logical_reasoning',
    'abstract_reasoning': 'c1_abstract_reasoning'
}

def generate_config_for_category(samples, main_cat, sub_cat, original_eval_json_path, video_base):
    """Generate updated configuration for a single subcategory"""
    original_config = {}
    if Path(original_eval_json_path).exists():
        with open(original_eval_json_path, 'r') as f:
            original_config = json.load(f)
    
    # Get the complete path of the subcategory directory
    folder_cat = CATEGORY_MAPPING.get(main_cat, main_cat)
    sub_dir = GVR_BASE / folder_cat / sub_cat
    
    # Create new configuration
    new_config = {}
    
    for sample in samples:
        sample_id = sample['id']
        
        # Get basic information from original configuration (if exists)
        original_sample = original_config.get(sample_id, {})
        
        # Build new sample configuration
        new_sample = original_sample.copy()
        
        # Update video path
        video_path = video_base / main_cat / sub_cat / f"{sample_id}.mp4"
        new_sample['generated_video_path'] = str(video_path)
        
        # Update input_image_path (relative to subcategory directory)
        if 'input_image_path' in original_sample:
            input_image_rel = original_sample['input_image_path']
            # If path contains input_images/, extract the part starting from that location
            if 'input_images/' in input_image_rel:
                parts = input_image_rel.split('input_images/')
                clean_path = 'input_images/' + parts[-1]
                new_sample['input_image_path'] = str(sub_dir / clean_path)
            else:
                new_sample['input_image_path'] = str(sub_dir / input_image_rel)
        
        # Update answer_image_path (relative to subcategory directory)
        if 'answer_image_path' in original_sample:
            answer_image_rel = original_sample['answer_image_path']
            # If path contains input_images/, extract the part starting from that location
            if 'input_images/' in answer_image_rel:
                parts = answer_image_rel.split('input_images/')
                clean_path = 'input_images/' + parts[-1]
                new_sample['answer_image_path'] = str(sub_dir / clean_path)
            else:
                new_sample['answer_image_path'] = str(sub_dir / answer_image_rel)
        
        # If last frame extraction is needed, add path
        if sample['needs_frame_extraction']:
            last_frame_path = video_base / main_cat / sub_cat / f"{sample_id}_last_frame.png"
            
            if sample['frame_crop_mode'] == 'full':
                new_sample['last_frame_image_path'] = str(last_frame_path)
            elif sample['frame_crop_mode'] == 'right_half':
                new_sample['last_frame_image_path_half'] = str(last_frame_path)
                # analogy also needs complete last frame
                new_sample['last_frame_image_path'] = str(last_frame_path)
            
            # Update gt_image_path (relative to subcategory directory)
            if 'gt_image_path' in original_sample:
                gt_image_rel = original_sample['gt_image_path']
                # If path contains input_images/, extract the part starting from that location
                if 'input_images/' in gt_image_rel:
                    parts = gt_image_rel.split('input_images/')
                    clean_path = 'input_images/' + parts[-1]
                    new_sample['gt_image_path'] = str(sub_dir / clean_path)
                else:
                    new_sample['gt_image_path'] = str(sub_dir / gt_image_rel)
        
        # Preserve prompt information
        if 'i2v_prompt' in original_sample:
            new_sample['i2v_prompt'] = original_sample['i2v_prompt']
        if 'eval_task_description' in original_sample:
            new_sample['eval_task_description'] = original_sample['eval_task_description']
        
        new_config[sample_id] = new_sample
    
    return new_config

def main():
    parser = argparse.ArgumentParser(description='Generate evaluation configuration files')
    parser.add_argument('--video-model', required=True,
                       help='Video model name, e.g.: wan2.5, sora2, veo3.1, seedance-pro, seedance-lite')
    parser.add_argument('--mode', choices=['batch', 'dimension', 'task'], default='batch',
                       help='Generation mode: batch(all), dimension(specified dimension), task(specified task)')
    parser.add_argument('--dimension', choices=['abstract', 'algorithmic', 'analogy', 'perceptual', 'planning', 'spatial'],
                       help='Dimension name (required for dimension and task modes)')
    parser.add_argument('--task', help='Task name (required for task mode)')
    args = parser.parse_args()
    
    video_model = args.video_model
    
    print("=" * 80)
    print(f"Step 2: Generate configuration JSON - {video_model} (Mode: {args.mode})")
    print("=" * 80)
    
    print("Loading dataset...")

    ds = load_dataset("ciciciciliu/Gen-Vire_ds")['train']
    # Dimension mapping
    dimension_mapping = {
        'abstract': 'abstract_reasoning',
        'algorithmic': 'algorithmic_logical_reasoning',
        'analogy': 'analogy_reasoning',
        'perceptual': 'perceptual_reasoning',
        'planning': 'planning_reasoning',
        'spatial': 'spatial_reasoning'
    }
    
    # Filter dataset by mode
    if args.mode == 'dimension':
        main_category = dimension_mapping[args.dimension]
        ds = [sample for sample in ds if sample['main_category'] == main_category]
        print(f"Dimension: {args.dimension} ({main_category})")
    elif args.mode == 'task':
        main_category = dimension_mapping[args.dimension]
        ds = [sample for sample in ds if sample['main_category'] == main_category and sample['sub_category'] == args.task]
        print(f"Task: {main_category}/{args.task}")
    
    print(f"Dataset size: {len(ds)} items")
    
    # Group by subcategory
    category_samples = defaultdict(list)
    for sample in ds:
        key = (sample['main_category'], sample['sub_category'])
        category_samples[key].append(sample)
    
    print(f"Number of subcategories: {len(category_samples)}")
    
    CONFIG_BASE_DIR = VIDEO_BASE_DIR / video_model / "temp_eval_configs"
    
    total_generated = 0
    
    # Outer loop: 5 subfolders
    for i in range(5):
        subfolder = f"{video_model}_{i}"
        VIDEO_BASE = VIDEO_BASE_DIR / video_model / subfolder
        OUTPUT_DIR = CONFIG_BASE_DIR / subfolder
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"Generating configuration: {subfolder}")
        print(f"{'='*80}")
        
        # Inner loop: each subcategory
        for (main_cat, sub_cat), samples in sorted(category_samples.items()):
            original_eval_json = Path(samples[0]['eval_json_path'])
            full_eval_json_path = GVR_BASE / original_eval_json
            
            new_config = generate_config_for_category(samples, main_cat, sub_cat, full_eval_json_path, VIDEO_BASE)
            
            output_file = OUTPUT_DIR / f"{main_cat}_{sub_cat}_eval.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)
            
            total_generated += 1
        
        print(f"  ✅ Generated {len(category_samples)} configuration files")
    
    print(f"\n{'='*80}")
    print("Generation completed")
    print(f"{'='*80}")
    print(f"Total generated: {total_generated} configuration files")
    print(f"Output directory: {CONFIG_BASE_DIR}")
if __name__ == "__main__":
    main()

# python step2_generate_configs.py --video-model wan2.5