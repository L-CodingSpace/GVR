#!/usr/bin/env python3
from datasets import load_dataset
from pathlib import Path
import shutil
import argparse
from typing import Callable, Any, List, Optional

def load_full_dataset():
    """Load complete dataset"""
    return load_dataset('ciciciciliu/Gen-Vire_ds')['train']

# Dimension mapping table
DIMENSION_MAPPING = {
    'abstract': 'abstract_reasoning',
    'algorithmic': 'algorithmic_logical_reasoning', 
    'analogy': 'analogy_reasoning',
    'perceptual': 'perceptual_reasoning',
    'planning': 'planning_reasoning',
    'spatial': 'spatial_reasoning'
}

def create_directory_structure(base_path: str, main_category: str, sub_category: str) -> Path:
    """Create directory structure"""
    target_dir = Path(base_path) / main_category / sub_category
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

def determine_video_filename(sample_id: str, sub_category: str, main_category: str) -> str:
    """Determine video filename based on category"""
    # Handle special naming rules
    if sub_category == 'symmetry':
        return f"random_{sample_id}"
    elif sub_category == 'color':
        # Map sample_id to specific color naming
        color_mapping = {'01': 'ColourBlue_42', '02': 'ColourBlue_43', '03': 'ColourRed_32'}
        return color_mapping.get(sample_id, f"Colour_{sample_id}")
    elif sub_category == 'reflect':
        # Special naming for reflection category
        reflect_mapping = {'01': 'ReflectY_19', '02': 'ReflectY_24', '03': 'ReflectY_43'}
        return reflect_mapping.get(sample_id, f"ReflectY_{sample_id}")
    elif sub_category == 'resize':
        # Special naming for resize category
        resize_mapping = {'01': 'Resize0.5XY_44', '02': 'Resize2XY_27', '03': 'Resize2XY_41'}
        return resize_mapping.get(sample_id, f"Resize_{sample_id}")
    else:
        # Use original ID by default
        return sample_id

def save_generated_video(video_data: Any, target_path: Path):
    """Save generated video to specified path"""
    # Users need to implement save logic based on their video format
    # This provides a generic interface
    if hasattr(video_data, 'save'):
        video_data.save(target_path)
    elif isinstance(video_data, (str, Path)):
        # If it's a file path, copy the file
        shutil.copy2(video_data, target_path)
    else:
        raise NotImplementedError("Please implement video saving logic")

def filter_dataset_by_mode(dataset: List, mode: str, dimension: Optional[str] = None, task: Optional[str] = None) -> List:
    """Filter dataset by mode"""
    if mode == 'batch':
        return dataset
    elif mode == 'dimension':
        if dimension not in DIMENSION_MAPPING:
            raise ValueError(f"Invalid dimension: {dimension}. Supported dimensions: {list(DIMENSION_MAPPING.keys())}")
        main_category = DIMENSION_MAPPING[dimension]
        return [sample for sample in dataset if sample['main_category'] == main_category]
    elif mode == 'task':
        if dimension not in DIMENSION_MAPPING:
            raise ValueError(f"Invalid dimension: {dimension}. Supported dimensions: {list(DIMENSION_MAPPING.keys())}")
        if not task:
            raise ValueError("Task mode requires specifying task parameter")
        main_category = DIMENSION_MAPPING[dimension]
        return [sample for sample in dataset if sample['main_category'] == main_category and sample['sub_category'] == task]
    else:
        raise ValueError(f"Invalid mode: {mode}. Supported modes: batch, dimension, task")

def benchmark_generate_videos_with_mode(
    video_model: str, 
    generate_function: Callable[[str, Any], Any],
    mode: str = 'batch',
    dimension: Optional[str] = None,
    task: Optional[str] = None
):
    """Benchmark video generation framework supporting multiple modes"""
    
    # 1. Load complete dataset
    print("Loading dataset...")
    full_dataset = load_full_dataset()
    
    # 2. Filter dataset by mode
    filtered_dataset = filter_dataset_by_mode(full_dataset, mode, dimension, task)
    print(f"Mode: {mode}, Filtered sample count: {len(filtered_dataset)}")
    
    # 3. Define output path (relative to project root)
    project_root = Path(__file__).parent.parent
    output_base = project_root / "0_generated_videos" / video_model
    
    # 4. Generate 5 videos for each sample
    total_generated = 0
    for sample in filtered_dataset:
        sample_id = sample['id']
        prompt = sample['i2v_prompt']
        image = sample['image']
        main_cat = sample['main_category']
        sub_cat = sample['sub_category']
        
        print(f"Generating sample {sample_id} ({main_cat}/{sub_cat})...")
        
        # Determine filename
        filename = determine_video_filename(sample_id, sub_cat, main_cat)
        
        # Generate videos for 5 batches
        for batch_idx in range(5):
            batch_output_base = output_base / f"{video_model}_{batch_idx}"
            
            # Create target directory
            target_dir = create_directory_structure(str(batch_output_base), main_cat, sub_cat)
            target_path = target_dir / f"{filename}.mp4"
            
            # Skip existing files
            if target_path.exists():
                continue
                
            # Call user generation function
            generated_video = generate_function(prompt, image)
            
            # Save generated video
            save_generated_video(generated_video, target_path)
            total_generated += 1
    
    print(f"Generation completed! Total generated {total_generated} video files")
    print(f"Output directory: {output_base}")

# Original function for backward compatibility
def benchmark_generate_videos(video_model: str, generate_function: Callable[[str, Any], Any]):
    """Original Benchmark video generation framework (backward compatible)"""
    return benchmark_generate_videos_with_mode(video_model, generate_function, mode='batch')

def example_user_generate_function(prompt: str, image: Any) -> Any:
    """Example user generation function - users need to implement their own generation logic"""
    # Example: user calls their own model
    # video = your_model.generate(prompt=prompt, image=image)
    # return video
    
    # This is just an example, users need to replace with their own implementation
    print(f"  Generating video - Prompt: {prompt[:50]}...")
    # Return an example path or video object
    return "/path/to/generated/video.mp4"

def main():
    """Main function - supports both command line and function call"""
    parser = argparse.ArgumentParser(description='Gen-ViRe Benchmark video generation framework')
    parser.add_argument('--video-model', required=True, help='Video model name')
    parser.add_argument('--mode', choices=['batch', 'dimension', 'task'], default='batch', 
                       help='Generation mode: batch(all), dimension(specified dimension), task(specified task)')
    parser.add_argument('--dimension', choices=['abstract', 'algorithmic', 'analogy', 'perceptual', 'planning', 'spatial'],
                       help='Dimension name (required for dimension and task modes)')
    parser.add_argument('--task', help='Task name (required for task mode)')
    
    args = parser.parse_args()
    
    # Parameter validation
    if args.mode in ['dimension', 'task'] and not args.dimension:
        parser.error(f"{args.mode} mode requires --dimension parameter")
    if args.mode == 'task' and not args.task:
        parser.error("task mode requires --task parameter")
    
    # Call generation function
    benchmark_generate_videos_with_mode(
        video_model=args.video_model,
        generate_function=example_user_generate_function,
        mode=args.mode,
        dimension=args.dimension,
        task=args.task
    )

# Function call examples
def usage_examples():
    """Usage examples"""
    # Batch mode - generate all samples
    benchmark_generate_videos_with_mode("my_model", example_user_generate_function, mode='batch')
    
    # Dimension mode - only generate abstract_reasoning category
    benchmark_generate_videos_with_mode("my_model", example_user_generate_function, mode='dimension', dimension='abstract')
    
    # Task mode - only generate spatial_reasoning/maze
    benchmark_generate_videos_with_mode("my_model", example_user_generate_function, mode='task', dimension='spatial', task='maze')

if __name__ == "__main__":
    main()
    
"""
0_generated_videos/{video_model}/
├── {video_model}_0/
│   ├── abstract_reasoning/
│   │   ├── 2d_rule_extrapolation/
│   │   │   ├── 01.mp4
│   │   │   ├── 02.mp4
│   │   │   └── 03.mp4
│   │   ├── 3d_rule_extrapolation/
│   │   ├── raven_matrix/
│   │   └── symmetry/
│   ├── algorithmic_logical_reasoning/
│   │   ├── cross_word/
│   │   ├── geometric_reasoning/
│   │   ├── graph_tr/
│   │   └── sudoku/
│   ├── analogy_reasoning/
│   │   ├── color/
│   │   ├── reflect/
│   │   ├── resize/
│   │   └── rotation/
│   ├── perceptual_reasoning/
│   │   ├── matching_color/
│   │   ├── matching_num/
│   │   ├── matching_pairs/
│   │   └── matching_shape/
│   ├── planning_reasoning/
│   │   ├── assemble_reasoning/
│   │   ├── gui_reasoning/
│   │   ├── multi_step_procedural_planning/
│   │   └── tool_use_selection/
│   └── spatial_reasoning/
│       ├── auto_drive/
│       ├── maze/
│       ├── spatial_obstacle/
│       └── vla/
├── {video_model}_1/ (same structure)
├── {video_model}_2/ (same structure)
├── {video_model}_3/ (same structure)
└── {video_model}_4/ (same structure)
"""