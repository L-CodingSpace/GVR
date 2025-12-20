#!/usr/bin/env python3
"""
Step 1: Batch extract all required last frames
"""

from datasets import load_dataset,load_from_disk
import cv2
from pathlib import Path
import argparse

# Configuration
VIDEO_BASE_DIR = Path(__file__).parent.parent / "0_generated_videos"

def extract_last_frame(video_path, output_path, crop_mode='full'):
    """Extract last frame from video"""
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        cap.release()
        raise ValueError(f"Video frame count is 0: {video_path}")
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError(f"Cannot read last frame: {video_path}")
    
    if crop_mode == 'right_half':
        h, w = frame.shape[:2]
        frame = frame[h//2:, w//2:]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), frame)

def main():
    parser = argparse.ArgumentParser(description='Batch extract last frames from videos')
    parser.add_argument('--video-model', required=True, 
                       help='Video model name, e.g.: wan2.5, sora2, veo3.1, seedance-pro, seedance-lite')
    parser.add_argument('--mode', choices=['batch', 'dimension', 'task'], default='batch',
                       help='Extraction mode: batch(all), dimension(specified dimension), task(specified task)')
    parser.add_argument('--dimension', choices=['abstract', 'algorithmic', 'analogy', 'perceptual', 'planning', 'spatial'],
                       help='Dimension name (required for dimension and task modes)')
    parser.add_argument('--task', help='Task name (required for task mode)')
    args = parser.parse_args()
    
    video_model = args.video_model
    
    print("=" * 80)
    print(f"Step 1: Batch extract last frames - {video_model} (Mode: {args.mode})")
    print("=" * 80)
    
    # Load dataset
    print("Loading dataset...")

    ds = load_dataset("ciciciciliu/Gen-Vire_ds")['train']
    needs_extraction = ds
    
    # Dimension mapping
    dimension_mapping = {
        'abstract': 'abstract_reasoning',
        'algorithmic': 'algorithmic_logical_reasoning',
        'analogy': 'analogy_reasoning',
        'perceptual': 'perceptual_reasoning',
        'planning': 'planning_reasoning',
        'spatial': 'spatial_reasoning'
    }
    
    # Filter samples by mode
    if args.mode == 'dimension':
        main_category = dimension_mapping[args.dimension]
        needs_extraction = [item for item in needs_extraction if item['main_category'] == main_category]
        print(f"Dimension: {args.dimension} ({main_category})")
    elif args.mode == 'task':
        main_category = dimension_mapping[args.dimension]
        needs_extraction = [item for item in needs_extraction 
                          if item['main_category'] == main_category and item['sub_category'] == args.task]
        print(f"Task: {main_category}/{args.task}")
    
    print(f"Dataset size: {len(ds)} items")
    print(f"Need to extract: {len(needs_extraction)} items")
    
    # Process 5 subfolders
    total_stats = {'full_success': 0, 'right_half_success': 0, 'total': 0}
    
    for i in range(5):
        subfolder = f"{video_model}_{i}"
        video_base = VIDEO_BASE_DIR / video_model / subfolder
        
        print(f"\n{'='*80}")
        print(f"Processing subfolder: {subfolder}")
        print(f"{'='*80}")
        
        stats = {'full_success': 0, 'right_half_success': 0}
        
        for sample in needs_extraction:
            main_cat = sample['main_category']
            sub_cat = sample['sub_category']
            sample_id = sample['id']
            crop_mode = sample['frame_crop_mode']
            
            video_path = video_base / main_cat / sub_cat / f"{sample_id}.mp4"
            output_path = video_base / main_cat / sub_cat / f"{sample_id}_last_frame.png"
            
            extract_last_frame(video_path, output_path, crop_mode)
            
            if crop_mode == 'full':
                stats['full_success'] += 1
            else:
                stats['right_half_success'] += 1
        
        # Subfolder statistics
        total_success = stats['full_success'] + stats['right_half_success']
        print(f"\n{subfolder} completed:")
        print(f"  - full mode: {stats['full_success']}")
        print(f"  - right_half mode: {stats['right_half_success']}")
        print(f"  - Total: {total_success}")
        
        total_stats['full_success'] += stats['full_success']
        total_stats['right_half_success'] += stats['right_half_success']
        total_stats['total'] += total_success
    
    # Total statistics
    print(f"\n{'='*80}")
    print("All completed")
    print(f"{'='*80}")
    print(f"Total processed: {total_stats['total']} frames")
    print(f"  - full mode: {total_stats['full_success']}")
    print(f"  - right_half mode: {total_stats['right_half_success']}")
    print(f"Output directory: {VIDEO_BASE_DIR / video_model}")

if __name__ == "__main__":
    main()

# python3 step1_extract_all_frames.py --video-model wan2.5
# python3 step1_extract_all_frames.py --video-model sora2
# python3 step1_extract_all_frames.py --video-model veo3.1


# ==========================================
# wan2.5/
# ├── wan2.5_0/
# │   └── abstract_reasoning/2d_rule_extrapolation/
# │       ├── 01.mp4
# │       ├── 01_last_frame.png  ← newly generated
# │       └── ...
# ├── wan2.5_1/
# ├── wan2.5_2/
# ├── wan2.5_3/
# └── wan2.5_4/
# ==========================================