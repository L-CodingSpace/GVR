#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
color_eval.py - 视觉类比评估脚本（颜色任务）
评分标准：模型答案与正确答案一致得1分，不一致得0 points
"""

from google import genai
import time
import json
from datetime import datetime
import os
import re
import sys

# ============================================
# 配置参数
# ============================================
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "ColourBlue_42"
config_filename = "color_eval.json"
model_name = "gemini-2.5-pro"

# 命令行参数解析（支持批量运行）
if '--task_id' in sys.argv:
    task_id = sys.argv[sys.argv.index('--task_id') + 1]
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]
if '--api_key' in sys.argv:
    API_KEY = sys.argv[sys.argv.index('--api_key') + 1]

# 固定使用简洁模式

# ============================================
# 路径设置
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
config_path = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)
prompt_path = os.path.join(SCRIPT_DIR, "..", "prompt_color.json")

# ============================================
# 读取配置
# ============================================
print("正在读取配置文件...")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 提取任务配置
task = config[task_id]
task_type = task["task_type"]
target_image_path = os.path.join(PROJECT_ROOT, task["last_frame_image_path_half"])
choices_image_path = os.path.join(PROJECT_ROOT, task["gt_image_path"])
correct_answer = task["correct_answer"]

# 提取提示词（优先从config，否则从prompt文件）
if "eval_task_description" in task:
    eval_prompt = task["eval_task_description"]
    i2v_prompt = task.get("i2v_prompt", "")
else:
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
    eval_prompt = prompt_config["eval_task_description"]
    i2v_prompt = prompt_config["i2v_prompt"]

print(f"✓ Task ID: {task_id}")
print(f"  任务类型: {task_type}")
print(f"  正确答案: {correct_answer}")
print(f"  目标图像: {target_image_path}")
print(f"  选项图像: {choices_image_path}\n")

# ============================================
# 初始化客户端
# ============================================
client = genai.Client(api_key=API_KEY)

# ============================================
# 上传图像
# ============================================
def upload_file(file_path, desc):
    print(f"上传 {desc}...")
    file_obj = client.files.upload(file=file_path)
    while file_obj.state.name == "PROCESSING":
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)
    print(f"✓ {desc} 就绪")
    return file_obj

target_file = upload_file(target_image_path, "目标图像")
choices_file = upload_file(choices_image_path, "选项图像")

# ============================================
# 调用 Gemini API
# ============================================
print("\n开始分析...")
response = client.models.generate_content(
    model=model_name,
    contents=[
        eval_prompt,
        "目标图像:",
        target_file,
        "选项图像:",
        choices_file
    ]
)

raw_response = response.text

# ============================================
# 解析答案
# ============================================
match = re.search(r'Final Answer:\s*([A-C]|different object type)', raw_response, re.IGNORECASE)

if match:
    model_answer = match.group(1).strip()
else:
    model_answer = "PARSE_ERROR"
    print("\n⚠️ 警告: 无法解析答案")

# ============================================
# 评 points
# ============================================
is_correct = (model_answer == correct_answer)
score = 1 if is_correct else 0

print("\n" + "=" * 50)
print("评分结果")
print("=" * 50)
print(f"正确答案: {correct_answer}")
print(f"模型答案: {model_answer}")
print(f"判定: {'✓ 正确' if is_correct else '✗ 错误'}")
print(f"Score: {score}/1")

# ============================================
# 保存结果
# ============================================
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_color")
if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)

result = {
    "task_id": task_id,
    "task_type": task_type,
    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "model": model_name,
    "correct_answer": correct_answer,
    "model_answer": model_answer,
    "is_correct": is_correct,
    "score": score,
    "normalized_score": score,  # 对于选择题，normalized_score 等于 score (0 或 1)
    "target_image": task["last_frame_image_path_half"],
    "choices_image": task["gt_image_path"]
}

# 保存 JSON
json_path = os.path.join(output_dir, f"{task_id}_score.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(f"\n✓ JSON Saved: {json_path}")

# 保存 TXT
txt_path = os.path.join(output_dir, f"{task_id}_score.txt")
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("视觉类比Evaluation Report\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"任务类型: {task_type}\n")
    f.write(f"评估时间: {result['timestamp']}\n")
    f.write(f"模型: {model_name}\n\n")
    f.write(f"正确答案: {correct_answer}\n")
    f.write(f"模型答案: {model_answer}\n")
    f.write(f"判定: {'正确' if is_correct else '错误'}\n")
    f.write(f"Score: {score}/1\n")
print(f"✓ TXT Saved: {txt_path}")

# ============================================
# 清理
# ============================================
client.files.delete(name=target_file.name)
client.files.delete(name=choices_file.name)

print("\n✓ 评估完成")

