#!/usr/bin/env python3
"""Generate evaluation results summary CSV"""

import json
import csv
from pathlib import Path
import argparse
from collections import defaultdict

def calculate_video_count(video_model, output_base, num_subfolders=5):
    """Calculate total number of videos"""
    count = 0
    for i in range(num_subfolders):
        subfolder = Path(output_base) / video_model / f"{video_model}_{i}"
        if subfolder.exists():
            for score_file in subfolder.rglob("*_score.json"):
                count += 1
    return count

def collect_scores(video_model, output_base, num_subfolders=5):
    """Collect all scores"""
    scores = defaultdict(lambda: defaultdict(list))
    
    for i in range(num_subfolders):
        subfolder = Path(output_base) / video_model / f"{video_model}_{i}"
        if not subfolder.exists():
            continue
        
        for score_file in subfolder.rglob("*_score.json"):
            with open(score_file, 'r') as f:
                data = json.load(f)
                score = data.get('normalized_score', 0)
                
                parts = score_file.relative_to(subfolder).parts
                if len(parts) >= 3:
                    main_cat = parts[0]
                    sub_cat = parts[1]
                    scores[main_cat][sub_cat].append(score)
    
    return scores

def generate_batch_csv(video_model, output_base):
    """Generate CSV for Batch mode"""
    scores = collect_scores(video_model, output_base)
    video_count = calculate_video_count(video_model, output_base)
    
    dim_scores = {}
    for main_cat, sub_cats in scores.items():
        all_scores = []
        for sub_scores in sub_cats.values():
            all_scores.extend(sub_scores)
        if all_scores:
            dim_scores[main_cat] = sum(all_scores) / len(all_scores)
    
    avg_score = sum(dim_scores.values()) / len(dim_scores) if dim_scores else 0
    
    csv_file = Path(output_base) / video_model / f"{video_model}_summary.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Methods', '#Videos', 'Avg.', 'Abstract', 'Algorithmic & Logical', 
                        'Analogy', 'Perceptual', 'Planning', 'Spatial'])
        
        row = [
            video_model,
            video_count,
            f"{avg_score:.3f}",
            f"{dim_scores.get('abstract_reasoning', 0):.3f}",
            f"{dim_scores.get('algorithmic_logical_reasoning', 0):.3f}",
            f"{dim_scores.get('analogy_reasoning', 0):.3f}",
            f"{dim_scores.get('perceptual_reasoning', 0):.3f}",
            f"{dim_scores.get('planning_reasoning', 0):.3f}",
            f"{dim_scores.get('spatial_reasoning', 0):.3f}",
        ]
        writer.writerow(row)
    
    print(f"✅ Generated Batch mode summary: {csv_file}")
    return csv_file

def generate_dimension_csv(video_model, dimension, output_base):
    """Generate CSV for Dimension mode"""
    base_dir = Path(output_base) / video_model / f"{video_model}_0" / dimension
    
    scores = defaultdict(list)
    video_count = 0
    
    for i in range(5):
        subfolder_base = Path(output_base) / video_model / f"{video_model}_{i}" / dimension
        if not subfolder_base.exists():
            continue
        
        for sub_cat_dir in subfolder_base.iterdir():
            if sub_cat_dir.is_dir():
                for score_file in sub_cat_dir.glob("*_score.json"):
                    with open(score_file, 'r') as f:
                        data = json.load(f)
                        score = data.get('normalized_score', 0)
                        scores[sub_cat_dir.name].append(score)
                        video_count += 1
    
    task_avg = {}
    for task, task_scores in scores.items():
        if task_scores:
            task_avg[task] = sum(task_scores) / len(task_scores)
    
    avg_score = sum(task_avg.values()) / len(task_avg) if task_avg else 0
    
    csv_file = Path(output_base) / video_model / f"{video_model}_{dimension}_summary.csv"
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['Methods', '#Videos', 'Avg.'] + sorted(task_avg.keys())
        writer.writerow(header)
        
        row = [video_model, video_count, f"{avg_score:.3f}"]
        for task in sorted(task_avg.keys()):
            row.append(f"{task_avg[task]:.3f}")
        writer.writerow(row)
    
    print(f"✅ Generated Dimension mode summary: {csv_file}")
    return csv_file

def generate_task_csv(video_model, main_category, sub_category, output_base):
    """Generate CSV for Task mode"""
    scores = []
    video_count = 0
    
    for i in range(5):
        subfolder = Path(output_base) / video_model / f"{video_model}_{i}" / main_category / sub_category
        if not subfolder.exists():
            continue
        
        for score_file in subfolder.glob("*_score.json"):
            with open(score_file, 'r') as f:
                data = json.load(f)
                score = data.get('normalized_score', 0)
                scores.append(score)
                video_count += 1
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    csv_file = Path(output_base) / video_model / f"{video_model}_{sub_category}_summary.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Methods', '#Videos', 'Score'])
        writer.writerow([video_model, video_count, f"{avg_score:.3f}"])
    
    print(f"✅ Generated Task mode summary: {csv_file}")
    return csv_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--video-model', required=True)
    parser.add_argument('--mode', required=True, choices=['batch', 'dimension', 'task'])
    parser.add_argument('--output-base', required=True)
    parser.add_argument('--dimension', default='')
    parser.add_argument('--main-category', default='')
    parser.add_argument('--sub-category', default='')
    args = parser.parse_args()
    
    if args.mode == 'batch':
        generate_batch_csv(args.video_model, args.output_base)
    elif args.mode == 'dimension':
        generate_dimension_csv(args.video_model, args.dimension, args.output_base)
    elif args.mode == 'task':
        generate_task_csv(args.video_model, args.main_category, args.sub_category, args.output_base)

if __name__ == "__main__":
    main()

