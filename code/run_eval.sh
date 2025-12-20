#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VIDEO_MODEL=""
MODE="batch"
DIMENSION=""
TASK=""

show_help() {
    cat << EOF
Usage: ./run_eval.sh --video-model <model> [--mode <mode>] [--dimension <dim>] [--task <task>]

Parameters:
  --video-model   Video model name (required)
  --mode          Evaluation mode: batch, dimension, task
                  Default: batch
  --dimension     Dimension name (required for dimension/task modes)
                  Options: abstract, algorithmic, perceptual, analogy, planning, spatial
  --task          Subcategory name (required only in task mode)

Examples:
  # Batch mode - evaluate all 24 subcategories
  ./run_eval.sh --video-model wan2.5
  ./run_eval.sh --video-model wan2.5 --mode batch

  # Dimension mode - evaluate 4 subcategories of a single dimension
  ./run_eval.sh --video-model wan2.5 --mode dimension --dimension abstract
  ./run_eval.sh --video-model wan2.5 --mode dimension --dimension analogy

  # Task mode - evaluate single subcategory
  ./run_eval.sh --video-model wan2.5 --mode task --dimension spatial --task maze
  ./run_eval.sh --video-model wan2.5 --mode task --dimension analogy --task color
EOF
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --video-model)
            VIDEO_MODEL="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --dimension)
            DIMENSION="$2"
            shift 2
            ;;
        --task)
            TASK="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown parameter '$1'"
            show_help
            exit 1
            ;;
    esac
done

if [ -z "$VIDEO_MODEL" ]; then
    echo "Error: Missing --video-model parameter"
    show_help
    exit 1
fi

if [ "$MODE" == "batch" ]; then
    echo "========================================"
    echo "Batch evaluation for all dimensions - $VIDEO_MODEL"
    echo "Mode: Batch (24 subcategories)"
    echo "========================================"
    python3 step3_batch_eval.py --video-model "$VIDEO_MODEL"
    
    echo ""
    echo "Generating summary CSV..."
    python3 step4_generate_summary.py \
        --video-model "$VIDEO_MODEL" \
        --mode batch \
        --output-base "../0_generated_videos"
    
elif [ "$MODE" == "dimension" ]; then
    if [ -z "$DIMENSION" ]; then
        echo "Error: dimension mode requires --dimension parameter"
        show_help
        exit 1
    fi
    
    SCRIPT=""
    MAIN_CAT=""
    case "$DIMENSION" in
        abstract)
            SCRIPT="step3_batch_eval_c1_abstract.py"
            DIM_NAME="C1 - Abstract Reasoning"
            MAIN_CAT="abstract_reasoning"
            ;;
        algorithmic)
            SCRIPT="step3_batch_eval_c2_algorithmic.py"
            DIM_NAME="C2 - Algorithmic Logical Reasoning"
            MAIN_CAT="algorithmic_logical_reasoning"
            ;;
        perceptual)
            SCRIPT="step3_batch_eval_c3_perceptual.py"
            DIM_NAME="C3 - Perceptual Reasoning"
            MAIN_CAT="perceptual_reasoning"
            ;;
        analogy)
            SCRIPT="step3_batch_eval_analogy_only.py"
            DIM_NAME="C4 - Analogy Reasoning"
            MAIN_CAT="analogy_reasoning"
            ;;
        planning)
            SCRIPT="step3_batch_eval_c5_planning.py"
            DIM_NAME="C5 - Planning Reasoning"
            MAIN_CAT="planning_reasoning"
            ;;
        spatial)
            SCRIPT="step3_batch_eval_c6_spatial.py"
            DIM_NAME="C6 - Spatial Reasoning"
            MAIN_CAT="spatial_reasoning"
            ;;
        *)
            echo "Error: Unknown dimension '$DIMENSION'"
            echo "Supported dimensions: abstract, algorithmic, perceptual, analogy, planning, spatial"
            exit 1
            ;;
    esac
    
    echo "========================================"
    echo "Evaluating single dimension - $VIDEO_MODEL"
    echo "Dimension: $DIM_NAME"
    echo "Mode: Dimension (4 subcategories)"
    echo "========================================"
    python3 "$SCRIPT" --video-model "$VIDEO_MODEL"
    
    echo ""
    echo "Generating summary CSV..."
    OUTPUT_DIR="../../new_results_${DIMENSION}"
    python3 step4_generate_summary.py \
        --video-model "$VIDEO_MODEL" \
        --mode dimension \
        --output-base "$OUTPUT_DIR" \
        --dimension "$MAIN_CAT"
    
elif [ "$MODE" == "task" ]; then
    if [ -z "$DIMENSION" ] || [ -z "$TASK" ]; then
        echo "Error: task mode requires --dimension and --task parameters"
        show_help
        exit 1
    fi
    
    MAIN_CAT=""
    case "$DIMENSION" in
        abstract)
            MAIN_CAT="abstract_reasoning"
            ;;
        algorithmic)
            MAIN_CAT="algorithmic_logical_reasoning"
            ;;
        perceptual)
            MAIN_CAT="perceptual_reasoning"
            ;;
        analogy)
            MAIN_CAT="analogy_reasoning"
            ;;
        planning)
            MAIN_CAT="planning_reasoning"
            ;;
        spatial)
            MAIN_CAT="spatial_reasoning"
            ;;
        *)
            echo "Error: Unknown dimension '$DIMENSION'"
            echo "Supported dimensions: abstract, algorithmic, perceptual, analogy, planning, spatial"
            exit 1
            ;;
    esac
    
    echo "========================================"
    echo "Evaluating single subcategory - $VIDEO_MODEL"
    echo "Category: $MAIN_CAT/$TASK"
    echo "Mode: Task (1 subcategory)"
    echo "========================================"
    python3 step3_batch_eval_single_task.py \
        --video-model "$VIDEO_MODEL" \
        --main-category "$MAIN_CAT" \
        --sub-category "$TASK"
    
    echo ""
    echo "Generating summary CSV..."
    python3 step4_generate_summary.py \
        --video-model "$VIDEO_MODEL" \
        --mode task \
        --output-base "../../new_results_single_task" \
        --main-category "$MAIN_CAT" \
        --sub-category "$TASK"
    
else
    echo "Error: Unknown mode '$MODE'"
    echo "Supported modes: batch, dimension, task"
    exit 1
fi

