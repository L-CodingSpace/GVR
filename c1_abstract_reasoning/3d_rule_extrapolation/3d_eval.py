#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
3d_eval.py - 3D Rule Reasoning任务评估脚本（使用 Gemini 2.5 Pro）
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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "01"  # 可修改为 "01", "02", "03"
config_filename = "3d_eval.json"
model_name = "gemini-2.5-pro"

# 命令行参数解析（支持批量运行）
if '--task_id' in sys.argv:
    task_id = sys.argv[sys.argv.index('--task_id') + 1]
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]
if '--api_key' in sys.argv:
    API_KEY = sys.argv[sys.argv.index('--api_key') + 1]

# 固定使用简洁模式

print(f"脚本目录: {SCRIPT_DIR}\n")

# ============================================
# 读取配置文件
# ============================================
json_path = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)
with open(json_path, "r", encoding="utf-8") as f:
    config = json.load(f)

task_config = config[task_id]

# 构建完整路径
input_image_path = task_config.get("input_image_path", "")
answer_image_path = task_config.get("answer_image_path", "")
last_frame_image_path = task_config.get("last_frame_image_path", "")
i2v_prompt = task_config.get("i2v_prompt", "N/A")
eval_task_description = task_config["eval_task_description"]
max_score = task_config.get("max_score", 8)

base_output_name = f"{task_id}_score"

print(f"✓ 任务配置: {task_id}")
print(f"  - Input Image: {input_image_path}")
print(f"  - Answer Image: {answer_image_path}")
print(f"  - Generated Image: {last_frame_image_path}")
print(f"  - 总分: {max_score}\n")

# ============================================
# 构建 Prompt
# ============================================
output_format_hint = """

# OUTPUT FORMAT:
Provide ONLY scores in JSON format:

{
  "Criterion_1": {"score": <value>},
  "Criterion_2": {"score": <value>}
  ...
}

Note: Think step-by-step internally, but only output final scores.
"""

full_prompt_text = eval_task_description + output_format_hint

# ============================================
# 初始化 Gemini 客户端
# ============================================
print("正在初始化 Gemini 客户端...")
client = genai.Client(api_key=API_KEY)
print("✓ 客户端初始化成功\n")

# ============================================
# 上传图片文件
# ============================================
def upload_and_wait(client, file_path, file_desc):
    print(f"上传 {file_desc}: {os.path.basename(file_path)}")
    file_obj = client.files.upload(file=file_path)
    
    while file_obj.state.name == "PROCESSING":
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)
    
    print(f"✓ {file_desc} 就绪")
    return file_obj

input_image_file = upload_and_wait(client, input_image_path, "输入图像")
answer_image_file = upload_and_wait(client, answer_image_path, "答案图像")
last_frame_file = upload_and_wait(client, last_frame_image_path, "生成图像")

print("\n✓ 所有图片上传完毕\n")

# ============================================
# 调用 API
# ============================================
print("正在调用 API 进行评估...\n")

response = client.models.generate_content(
    model=model_name,
    contents=[
        full_prompt_text,
        "【Input Image】 (Original Problem):",
        input_image_file,
        "【Ground Truth Image】 (Correct Solution):",
        answer_image_file,
        "【Final Frame Image】 (Generated Solution):",
        last_frame_file
    ]
)

print("✓ API 调用完成\n")

# ============================================
# 解析结果
# ============================================
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_3d")
if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)

clean_text = response.text.strip().replace("```json\n", "").replace("```", "")
result_json = json.loads(clean_text)

print("=" * 60)
print("3D Rule Reasoning评估结果")
print("=" * 60)
print(json.dumps(result_json, indent=2, ensure_ascii=False))

# ============================================
# 计算总 points
# ============================================
total_score = 0
criterion_count = 0

for key, value in result_json.items():
    if "Criterion" in key and isinstance(value, dict):
        score = value.get("score", 0)
        total_score += score
        criterion_count += 1

normalized_score = total_score / max_score if max_score > 0 else 0

result_json["total_score"] = total_score
result_json["max_score"] = max_score
result_json["normalized_score"] = round(normalized_score, 4)
result_json["criterion_count"] = criterion_count
result_json["task_id"] = task_id

print("\n" + "=" * 60)
print("Score Summary")
print("=" * 60)
print(f"Total Score: {total_score}/{max_score}")
print(f"Normalized Score: {normalized_score:.4f}")
print(f"Percentage Score: {normalized_score * 100:.2f}分\n")

# ============================================
# 保存 JSON
# ============================================
json_output_filename = os.path.join(output_dir, f"{base_output_name}.json")
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"✓ JSONSaved: {json_output_filename}")

# ============================================
# 保存 TXT Report
# ============================================
txt_output_filename = os.path.join(output_dir, f"{base_output_name}.txt")

usage = response.usage_metadata
cost_input = usage.prompt_token_count / 1_000_000 * 1.25
cost_output = usage.candidates_token_count / 1_000_000 * 5.00
total_cost = cost_input + cost_output

with open(txt_output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("3D Rule ReasoningEvaluation Report (3D Rule Extrapolation Evaluation)\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"Model: {model_name}\n")
    mode_str = "简洁模式 (Concise Mode)"
    f.write(f"Evaluation Mode: {mode_str}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Token Usage Statistics\n")
    f.write("=" * 60 + "\n")
    f.write(f"Input tokens: {usage.prompt_token_count}\n")
    f.write(f"Output tokens: {usage.candidates_token_count}\n")
    f.write(f"Total tokens: {usage.total_token_count}\n")
    f.write(f"Estimated Cost: ${total_cost:.6f} USD\n\n")
    
    f.write(f"I2V Prompt:\n{i2v_prompt}\n\n")
    
    f.write(f"Input Image: {input_image_path}\n")
    f.write(f"Answer Image: {answer_image_path}\n")
    f.write(f"Generated Image: {last_frame_image_path}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Score Summary\n")
    f.write("=" * 60 + "\n")
    f.write(f"Total Score: {total_score}/{max_score}\n")
    f.write(f"Normalized Score: {normalized_score:.4f}\n")
    f.write(f"Percentage Score: {normalized_score * 100:.2f}分\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Detailed Scores and Reasons\n")
    f.write("=" * 60 + "\n\n")
    
    criterion_names = {
        "Criterion_1": "Correctness of Solution (Correctness of Solution)",
        "Criterion_2": "放置准确性 (Accuracy of Solution Placement)",
        "Criterion_3": "Environment Stability (Environment Stability)"
    }
    
    for key in ["Criterion_1", "Criterion_2", "Criterion_3"]:
        if key in result_json:
            criterion = result_json[key]
            f.write(f"{key}: {criterion_names[key]}\n")
            f.write(f"Score: {criterion['score']}\n")
            f.write(f"Reason:\n{criterion.get('reason', 'No reason provided')}\n\n")
            f.write("-" * 60 + "\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Full API Response\n")
    f.write("=" * 60 + "\n")
    f.write(response.text)

print(f"✓ ReportSaved: {txt_output_filename}\n")

# ============================================
# Cleaning uploaded files
# ============================================
print("Cleaning uploaded files...")
client.files.delete(name=input_image_file.name)
client.files.delete(name=answer_image_file.name)
client.files.delete(name=last_frame_file.name)
print("✓ Cleanup completed\n")

print("=" * 60)
print("✓ Script Execution Completed")
print("=" * 60)

