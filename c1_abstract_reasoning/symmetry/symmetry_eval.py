#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sym_eval.py - Symmetry视频评估脚本（使用 Gemini 2.5 Pro）
使用已提取的最后一帧，对比GT图像进行评估
"""

from google import genai
import time
import json
from datetime import datetime
import os
import sys

# ============================================
# 配置参数
# ============================================
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "random_03"
path_config_filename = "sym_path.json"
prompt_config_filename = "sym_prompt.json"
config_filename = "symmetry_eval.json"  # 新增：统一配置文件
model_name = "gemini-2.5-pro"

# 命令行参数解析（支持批量运行）
if '--task_id' in sys.argv:
    task_id = sys.argv[sys.argv.index('--task_id') + 1]
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]
if '--api_key' in sys.argv:
    API_KEY = sys.argv[sys.argv.index('--api_key') + 1]
    path_config_filename = config_filename  # 使用统一配置
    prompt_config_filename = config_filename

# 固定使用简洁模式

# ============================================
# 获取脚本所在目录
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"脚本目录: {SCRIPT_DIR}\n")

# ============================================
# 读取配置文件
# ============================================
print("正在读取配置文件...")

# 支持统一配置文件格式（新）和分离配置（旧）
config_json = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)

# 尝试读取统一配置
if os.path.exists(config_json):
    with open(config_json, "r", encoding="utf-8") as f:
        config = json.load(f)
    task = config[task_id]
    
    # 路径处理
    input_image_path = task.get("input_image_path", "")
    gt_image_path = task.get("gt_image_path", "")
    video_path = task.get("generated_video_path", "")
    last_frame_path = task.get("last_frame_image_path", "")
    
    # Prompt 处理（可能在任务配置内，也可能在单独字段）
    eval_prompt = task.get("eval_task_description") or task.get("eval_system_prompt", "")
    i2v_prompt = task.get("i2v_prompt", "")
else:
    # 回退到旧的分离配置格式
    path_json = os.path.join(SCRIPT_DIR, path_config_filename)
    with open(path_json, "r", encoding="utf-8") as f:
        path_config = json.load(f)
    
    prompt_json = os.path.join(SCRIPT_DIR, prompt_config_filename)
    with open(prompt_json, "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
    
    task = path_config[task_id]
    input_image_path = os.path.join(SCRIPT_DIR, task["input_image_path"])
    gt_image_path = os.path.join(SCRIPT_DIR, task["gt_image_path"])
    video_path = os.path.join(SCRIPT_DIR, task["generated_video_path"])
    last_frame_path = os.path.join(SCRIPT_DIR, task["last_frame_image_path"])
    
    eval_prompt = prompt_config["eval_task_description"]
    i2v_prompt = prompt_config["i2v_prompt"]

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - Input Image: {input_image_path}")
print(f"  - GT图像: {gt_image_path}")
print(f"  - 生成视频: {video_path}")
print(f"  - 最后一帧: {last_frame_path}\n")

# 基于任务ID创建输出文件名
base_output_name = f"{task_id}_score"

# ============================================
# 初始化Gemini客户端
# ============================================
client = genai.Client(api_key=API_KEY)

# ============================================
# 上传文件
# ============================================
def upload_and_wait(client, file_path, file_desc):
    print(f"正在上传 {file_desc} '{os.path.basename(file_path)}'...")
    file_obj = client.files.upload(file=file_path)
    
    while file_obj.state.name == "PROCESSING":
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)
    
    print(f"✓ {file_desc} 文件就绪")
    return file_obj

gt_image_file = upload_and_wait(client, gt_image_path, "GT图像")
generated_frame_file = upload_and_wait(client, last_frame_path, "生成帧")

print("\n✓ 2个图像均已上传，开始分析...\n")

# ============================================
# 根据模式构建评估提示
# ============================================
output_format_hint = """

# OUTPUT FORMAT:
Please provide your evaluation in JSON format with ONLY scores:

{
  "Criterion_1": {"score": <0 or 1>},
  "Criterion_2": {"score": <0 or 1>},
  "Criterion_3": {"score": <0 or 1>}
  ...
}

Note: Think step-by-step internally, but only output final scores.
"""

final_eval_prompt = eval_prompt + output_format_hint

# ============================================
# 调用API生成内容
# ============================================
response = client.models.generate_content(
    model=model_name,
    contents=[
        final_eval_prompt,
        "【标准答案图像】(Ground-Truth Image):",
        gt_image_file,
        "【生成帧图像】(Generated Frame Image):",
        generated_frame_file
    ]
)

# ============================================
# 输出分析结果
# ============================================
print("=" * 50)
print("Symmetry视频分析结果")
print("=" * 50)

output_dir = os.path.join(SCRIPT_DIR, "analysis_results_symmetry")

if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)

clean_text = response.text.strip().replace("```json\n", "").replace("```", "")
result_json = json.loads(clean_text)

print("解析结果 (JSON):")
print(json.dumps(result_json, indent=2, ensure_ascii=False))

# ============================================
# 计算归一化分数
# ============================================
total_score = 0
criterion_count = 0

for key, value in result_json.items():
    if key.startswith("Criterion_") and isinstance(value, dict):
        score = value.get("score", 0)
        total_score += score
        criterion_count += 1

normalized_score = total_score / criterion_count if criterion_count > 0 else 0

result_json["normalized_score"] = round(normalized_score, 4)
result_json["total_score"] = total_score
result_json["criterion_count"] = criterion_count
result_json["task_id"] = task_id

print("\n--- Score Summary ---")
print(f"各项Score: {total_score}/{criterion_count}")
print(f"Normalized Score: {normalized_score:.4f} (0-1范围)")
print(f"Percentage Score: {normalized_score * 100:.2f}分")

# 保存JSON
json_output_filename = os.path.join(output_dir, f"{task_id}_score.json")
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")

# ============================================
# 保存到txt文件
# ============================================
txt_output_filename = os.path.join(output_dir, f"{task_id}_score.txt")

usage = response.usage_metadata
print(f"\nInput tokens: {usage.prompt_token_count}")
print(f"Output tokens: {usage.candidates_token_count}")
print(f"Total tokens: {usage.total_token_count}")

cost_input = usage.prompt_token_count / 1_000_000 * 1.25
cost_output = usage.candidates_token_count / 1_000_000 * 5.00
total_cost = cost_input + cost_output
print(f"Estimated Cost: ${total_cost:.6f} USD")

with open(txt_output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("Symmetry视频分析Report\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"Model: {model_name}\n")
    mode_str = "简洁模式 (Concise Mode)"
    f.write(f"Evaluation Mode: {mode_str}\n\n")

    f.write("=" * 50 + "\n")
    f.write("Token Usage Statistics\n")
    f.write("=" * 50 + "\n")
    f.write(f"Input tokens: {usage.prompt_token_count}\n")
    f.write(f"Output tokens: {usage.candidates_token_count}\n")
    f.write(f"Total tokens: {usage.total_token_count}\n")
    f.write(f"Estimated Cost: ${total_cost:.6f} USD\n\n")
    
    f.write(f"I2V Prompt: {i2v_prompt}\n\n")

    f.write(f"Input Image: {input_image_path}\n")
    f.write(f"GT图像: {gt_image_path}\n")
    f.write(f"生成视频: {video_path}\n")
    f.write(f"评估帧: {last_frame_path}\n\n")
    
    f.write(f"GT图像 (File ID): {gt_image_file.name}\n")
    f.write(f"生成帧 (File ID): {generated_frame_file.name}\n\n")

    f.write("=" * 50 + "\n")
    f.write("分析Prompt - Symmetry评估\n")
    f.write("=" * 50 + "\n")
    f.write(eval_prompt + "\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("Score Summary\n")
    f.write("=" * 50 + "\n")
    f.write(f"各项Score: {total_score}/{criterion_count}\n")
    f.write(f"Normalized Score: {normalized_score:.4f} (0-1范围)\n")
    f.write(f"Percentage Score: {normalized_score * 100:.2f}分\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("分析结果 (原始文本)\n")
    f.write("=" * 50 + "\n")
    f.write(response.text)

print(f"✓ 完整Report已保存到: {txt_output_filename}")

# ============================================
# Cleaning uploaded files
# ============================================
print("\n正在Cleaning uploaded files...")
client.files.delete(name=gt_image_file.name)
client.files.delete(name=generated_frame_file.name)

print("\n✓ Script Execution Completed")

