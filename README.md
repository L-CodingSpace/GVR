# Can World Simulators Reason? Gen-ViRe: A Generative Visual Reasoning Benchmark

<p align="center">
  <a href="https://arxiv.org/pdf/2511.13853">
    <img src="https://img.shields.io/badge/Gen--ViRe-2511.13853-b31b1b.svg" alt="Paper">
  </a>
  <a href="https://l-codingspace.github.io/gvr_web/">
    <img src="https://img.shields.io/badge/Gen--ViRe-Project%20Page-green.svg" alt="Project Page">
  </a>
  <a href="https://huggingface.co/datasets/ciciciciliu/Gen-Vire_ds">
    <img src="https://img.shields.io/badge/Gen--ViRe-🤗Data-yellow.svg" alt="🤗Data">
  </a>
  <a href="LICENSE-Apache">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License">
  </a>
</p>

Gen-ViRe is a comprehensive video reasoning capability assessment benchmark for testing and evaluating the performance of video generation models on various reasoning tasks.

## 🎯 Benchmark Overview

### Evaluation Dimensions

The Gen-ViRe benchmark contains the following 6 core reasoning dimensions:

| Dimension | Number of Subcategories |
|-----------|-------------------------|
| Abstract Reasoning | 4 |
| Algorithmic & Logical Reasoning | 4 |
| Perceptual Reasoning | 4 |
| Analogy Reasoning | 4 |
| Planning Reasoning | 4 |
| Spatial Reasoning | 4 |

### Detailed Subcategories

#### Abstract Reasoning
- `2d_rule_extrapolation` - 2D Rule Extrapolation
- `3d_rule_extrapolation` - 3D Rule Extrapolation  
- `raven_matrix` - Raven's Progressive Matrices
- `symmetry` - Symmetry

#### Algorithmic & Logical Reasoning
- `cross_word` - Crossword Puzzle
- `geometric_reasoning` - Geometric Reasoning
- `graph_tr` - Graph Traversal
- `sudoku` - Sudoku

#### Perceptual Reasoning
- `matching_color` - Color Matching
- `matching_num` - Number Matching
- `matching_pairs` - Pair Matching
- `matching_shape` - Shape Matching

#### Analogy Reasoning
- `color` - Color Transformation
- `reflect` - Reflection Transformation
- `resize` - Scaling Transformation
- `rotation` - Rotation Transformation

#### Planning Reasoning
- `assemble_reasoning` - Assembly Reasoning
- `gui_reasoning` - GUI Reasoning
- `multi_step_procedural_planning` - Multi-step Procedural Planning
- `tool_use_selection` - Tool Use Selection

#### Spatial Reasoning
- `auto_drive` - Autonomous Driving
- `maze` - Maze Navigation
- `spatial_obstacle` - Spatial Obstacle
- `vla` - Vision-Language-Action

## 🚀 Quick Start

### Environment Requirements

```bash
# Activate conda environment
conda activate vr_desk

# Python dependencies
pip install datasets opencv-python pathlib argparse

# Valid Gemini 2.5 Pro API **key required for evaluation**
export GEMINI_API_KEY="your_api_key_here"
```
****
## 📁 Project Structure

```
Gen-ViRe/
├── code/                           # Core code
│   ├── run_all_steps.sh           # One-click run script
│   ├── sample_psdl.py             # Video generation framework example
│   ├── step0_reorganize_videos.py # Video file reorganization
│   ├── step1_extract_all_frames.py# Frame extraction
│   ├── step2_generate_configs.py  # Configuration generation
│   ├── step3_batch_eval.py        # Batch evaluation
│   └── step4_generate_summary.py  # Result summarization
├── c1_abstract_reasoning/         # Abstract reasoning dimension evaluation scripts
│   ├── 2d_rule_extrapolation/
│   ├── 3d_rule_extrapolation/
│   ├── raven_matrix/
│   └── symmetry/
├── c2_algorithmic_logical_reasoning/ # Algorithmic logical reasoning dimension evaluation scripts
├── c3_perceptural_reasoning/      # Perceptual reasoning dimension evaluation scripts
├── c4_analogy_resoning/           # Analogy reasoning dimension evaluation scripts
├── c5_planing_reasoning/          # Planning reasoning dimension evaluation scripts
├── c6_spatial_reasoning/          # Spatial reasoning dimension evaluation scripts
└── 0_generated_videos/            # Generated videos and evaluation results
    └── {model_name}/
        ├── {model_name}_0/        # 1st run results
        ├── {model_name}_1/        # 2nd run results
        ├── {model_name}_2/        # 3rd run results
        ├── {model_name}_3/        # 4th run results
        ├── {model_name}_4/        # 5th run results
        └── temp_eval_configs/     # Evaluation configuration files
```

## 🎬 Video Generation Integration

### Using the Example Framework

**Step 1**: Open the `code/sample_psdl.py` file

**Step 2**: Find the `example_user_generate_function` function (line 141), replace it with your video generation logic:

```python
def example_user_generate_function(prompt: str, image: Any) -> Any:
    """Example user generation function - users need to implement their own generation logic"""
    # Replace this code with your model call
    video = your_model.generate(prompt=prompt, image=image)
    return video  # Return video file path or video object
```

**Step 3**: Run the generation script:

```**bash**
cd code/
python3 sample_psdl.py --video-model your_model_name --mode batch
```
****
This will generate videos for all 72 samples (5 versions per sample), automatically saved to the correct directory structure (there are three different generation modes, see below).****

### Supported Generation Modes

#### Batch Mode - Generate All Samples

**Command:**
```bash
cd code/
python3 sample_psdl.py --video-model your_model_name --mode batch
```

**Generated File Structure:**
```
0_generated_videos/your_model_name/
├── your_model_name_0/
│   ├── abstract_reasoning/
│   │   ├── 2d_rule_extrapolation/
│   │   │   ├── 01.mp4
│   │   │   ├── 02.mp4
│   │   │   └── 03.mp4
│   │   ├── 3d_rule_extrapolation/
│   │   ├── raven_matrix/
│   │   └── symmetry/
│   ├── algorithmic_logical_reasoning/
│   ├── perceptual_reasoning/
│   ├── analogy_reasoning/
│   ├── planning_reasoning/
│   └── spatial_reasoning/
├── your_model_name_1/ (same structure)
├── your_model_name_2/ (same structure)
├── your_model_name_3/ (same structure)
└── your_model_name_4/ (same structure)
```
#### Dimension Mode - Generate Specified Dimension

**Command:**
```bash
cd code/
python3 sample_psdl.py --video-model your_model_name --mode dimension --dimension abstract
```

**Generated File Structure:**
```
0_generated_videos/your_model_name/
├── your_model_name_0/
│  ** └── abstract_reasoning/
│       ├── 2d_rule_extrapolation/
│       │   ├── 01.mp4
│       │   ├── 02.mp4
│       │   └── 03.mp4
│       ├── 3d_rule_extrapolation/
│       ├── raven_matrix/
│       └── symmetry/
├── your_model_name_1/ (same structure)
├── your_model_name_2/ (same structure)
├── your_model_name_3/ (same structure)
└── your_model_name_4/ (same structure)
```**

#### Task Mode - Generate Single Task

**Command:**
```bash
cd code/
python3 sample_psdl.py --video-model your_model_name --mode task --dimension spatial --task maze
```

**Generated File Structure:**
```
0_generated_videos/your_model_name/
├── your_model_name_0/
│   └── spatial_reasoning/
│       └── maze/
│           ├── 01.mp4
│           ├── 02.mp4
│           └── 03.mp4
├── your_model_name_1/
│   └── spatial_reasoning/
│       └── maze/
├── your_model_name_2/
├── your_model_name_3/
└── your_model_name_4/
```


## 📊 **Evaluation Process**

### Prerequisites (Required)

After generating videos, you need to complete the following two steps first. **Note: The mode for prerequisites must match the mode used for video generation.**

#### Prerequisites for Batch Mode

```bash
cd code/

# Step 1: Extract last frame from videos
python3 step1_extract_all_frames.py --video-model your_model_name --mode batch

# Step 2: Generate evaluation configuration files
python3 step2_generate_configs.py --video-model your_model_name --mode batch
```

#### Prerequisites for Dimension Mode

```bash
cd code/

# Step 1: Extract last frame from videos
python3 step1_extract_all_frames.py --video-model your_model_name --mode dimension --dimension abstract

# Step 2: Generate evaluation configuration files
python3 step2_generate_configs.py --video-model your_model_name --mode dimension --dimension abstract
```

#### Prerequisites for Task Mode

```bash
cd code/

# Step 1: Extract last frame from videos
python3 step1_extract_all_frames.py --video-model your_model_name --mode task --dimension spatial --task maze

# Step 2: Generate evaluation configuration files
python3 step2_generate_configs.py --video-model your_model_name --mode task --dimension spatial --task maze
```

### Three Evaluation Modes

After completing the prerequisites, you can choose from the following three evaluation modes:

#### Mode 1: Evaluate All 24 Tasks Across 6 Dimensions (Batch Mode)

```bash
cd code/
./run_eval.sh --video-model your_model_name
# Or explicitly specify batch mode
./run_eval.sh --video-model your_model_name --mode batch
```

**Expected Output:**
- Output directory: `0_generated_videos/{model_name}/`
- Evaluate all 24 subcategories (6 dimensions × 4 subcategories)
- Generate summary file: `{model_name}_summary.csv`

#### Mode 2: Evaluate 4 Tasks Under Specific Dimension (Dimension Mode)

```bash
cd code/
# Evaluate 4 tasks in abstract reasoning dimension
./run_eval.sh --video-model your_model_name --mode dimension --dimension abstract


# Evaluate 4 tasks in spatial reasoning dimension
./run_eval.sh --video-model your_model_name --mode dimension --dimension spatial
```

**Expected Output:**
- Output directory: `new_results_{dimension}/{model_name}/`
- Only evaluate 4 subcategories of the specified dimension
- Generate dimension summary file: `{model_name}_{dimension}_summary.csv`

#### Mode 3: Evaluate Specific Task (Task Mode)

```bash
cd code/
# Evaluate maze task under spatial reasoning dimension
./run_eval.sh --video-model your_model_name --mode task --dimension spatial --task maze

# Evaluate color transformation task under analogy reasoning dimension
./run_eval.sh --video-model your_model_name --mode task --dimension analogy --task color
```

**Expected Output:**
- Output directory: `0_generated_videos/{model_name}/`
- Only evaluate the specified single subcategory task
- Generate task summary file: `{model_name}_{task}_summary.csv`


## 🎯 **Complete Usage Examples**

### Batch Mode - Complete Workflow

```bash
cd code/

# 1. Generate all videos
python3 sample_psdl.py --video-model my_model --mode batch

# 2. Extract frames
python3 step1_extract_all_frames.py --video-model my_model --mode batch

# 3. Generate configurations
python3 step2_generate_configs.py --video-model my_model --mode batch

# 4. Evaluate
./run_eval.sh --video-model my_model --mode batch
```

### Dimension Mode - Complete Workflow

```bash
cd code/

# 1. Generate videos for specified dimension
python3 sample_psdl.py --video-model my_model --mode dimension --dimension abstract

# 2. Extract frames
python3 step1_extract_all_frames.py --video-model my_model --mode dimension --dimension abstract

# 3. Generate configurations
python3 step2_generate_configs.py --video-model my_model --mode dimension --dimension abstract

# 4. Evaluate
./run_eval.sh --video-model my_model --mode dimension --dimension abstract
```

### Task Mode - Complete Workflow

```bash
cd code/

# 1. Generate videos for specified task
python3 sample_psdl.py --video-model my_model --mode task --dimension spatial --task maze

# 2. Extract frames
python3 step1_extract_all_frames.py --video-model my_model --mode task --dimension spatial --task maze

# 3. Generate configurations
python3 step2_generate_configs.py --video-model my_model --mode task --dimension spatial --task maze

# 4. Evaluate
./run_eval.sh --video-model my_model --mode task --dimension spatial --task maze
```

## 📖 Citation

If you find Gen-ViRe useful for your research, please cite our work:

```bibtex
@article{liu2025can,
  title={Can World Simulators Reason? Gen-ViRe: A Generative Visual Reasoning Benchmark},
  author={Liu, Xinxin and Xu, Zhaopan and Wang, Kai and Lee, Yong Jae and Shang, Yuzhang},
  journal={arXiv preprint arXiv:2511.13853},
  year={2025}
}
```

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE-Apache](LICENSE-Apache) file for details.


