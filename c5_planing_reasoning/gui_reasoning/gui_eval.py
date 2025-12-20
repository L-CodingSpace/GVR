#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================
# 导入库
# ============================================
from google import genai
import time
import json
from datetime import datetime
import os
import re
import sys

# ============================================
# 获取脚本所在目录，确保路径正确
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
print(f"脚本目录: {SCRIPT_DIR}")
print(f"项目根目录: {PROJECT_ROOT}\n")

# ============================================
# 配置参数
# ============================================
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "01"  # 可以修改为 "01", "02", "03", "04", "05"
config_filename = "gui_eval.json"

# 命令行参数解析（支持批量运行）
if '--task_id' in sys.argv:
    task_id = sys.argv[sys.argv.index('--task_id') + 1]
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]
if '--api_key' in sys.argv:
    API_KEY = sys.argv[sys.argv.index('--api_key') + 1]


# 固定使用简洁模式

# ============================================
# 读取配置文件
# ============================================
print(f"正在加载任务: {task_id}...")
config_path = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 提取特定任务的配置
if task_id not in config:
    print(f"❌ 错误: 在 'gui_eval.json' 中找不到任务 ID: {task_id}")
    exit(1)

task_config = config[task_id]

# 从配置中动态获取path（将相对路径转换为绝对路径）
video_path = task_config.get("generated_video_path", "")
if not video_path:
    print("❌ 配置中未找到 generated_video_path")
    exit(1)
video_file_name = os.path.basename(video_path)

# 提取配置信息
input_image_path_rel = task_config.get("input_image_path", "")
input_image_path = os.path.join(SCRIPT_DIR, input_image_path_rel) if input_image_path_rel else None
i2v_prompt = task_config.get("i2v_prompt", "")
eval_task_description = task_config.get("eval_task_description", "")

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - 视频路径: {video_path}")
if input_image_path:
    print(f"  - 输入图片: {input_image_path}")
print(f"  - I2V提示词: {i2v_prompt}\n")

# ============================================
# 使用配置中的评估描述作为 Prompt
# ============================================
autorater_prompt = eval_task_description

# ============================================
# 初始化Gemini客户端
# ============================================
print("正在初始化Gemini客户端...")
client = genai.Client(api_key=API_KEY)
model_name = "gemini-2.5-pro"

# 命令行参数解析（支持批量运行）
if '--task_id' in sys.argv:
    task_id = sys.argv[sys.argv.index('--task_id') + 1]
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]
if '--api_key' in sys.argv:
    API_KEY = sys.argv[sys.argv.index('--api_key') + 1]
print(f"✓ Gemini客户端初始化成功, Model: {model_name}\n")

# ============================================
# 上传视频文件
# ============================================
print(f"正在上传视频 '{video_file_name}'...")
if not os.path.exists(video_path):
    print(f"❌ 视频文件未找到: {video_path}")
    exit(1)

video_file = client.files.upload(file=video_path)
print(f"✓ 上传成功，文件ID: {video_file.name}")

# ============================================
# 等待文件处理完成（关键步骤）
# ============================================
print("等待文件处理...")
while video_file.state.name == "PROCESSING":
    time.sleep(2)
    video_file = client.files.get(name=video_file.name)
    print(f"  状态: {video_file.state.name}")

if video_file.state.name == "FAILED":
    print("❌ 文件处理失败")
    exit(1)

print("✓ 文件就绪，开始分析\n")

# ============================================
# 调用API生成内容
# ============================================
print("正在调用API... (这可能需要一些时间)")
response = client.models.generate_content(
    model=model_name,
    contents=[autorater_prompt, video_file]
)
print("✓ API调用完成\n")

# ============================================
# 输出分析结果到终端
# ============================================
print("=" * 50)
print("分析结果")
print("=" * 50)

# 准备输出文件路径
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_gui")
if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)
json_output_filename = os.path.join(output_dir, f"{task_id}_score.json")
txt_output_filename = os.path.join(output_dir, f"{task_id}_score.txt")

# 清理并解析JSON
raw_text = response.text.strip()
clean_text = raw_text.replace("```json", "").replace("```", "").strip()

# 尝试从文本中提取JSON部 points
json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
if json_match:
    clean_text = json_match.group(0)

try:
    result_json = json.loads(clean_text)
    result_json['normalized_score'] = result_json['overall_score']
except json.JSONDecodeError as e:
    print(f"\n❌ JSON解析失败: {e}")
    print(f"错误位置: 第{e.lineno}行, 第{e.colno}列")
    debug_file = os.path.join(output_dir, f"{task_id}_debug_raw.txt")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print(f"原始响应已保存到: {debug_file}")
    print(f"\n原始响应内容预览:")
    print(raw_text[:500] if len(raw_text) > 500 else raw_text)
    raise

print("解析结果 (JSON):")
print(json.dumps(result_json, indent=2, ensure_ascii=False))

# 提取关键信息
overall_score = result_json.get("overall_score", "N/A")
summary = result_json.get("evaluation_summary", "No summary provided.")

print("\n--- 简易摘要 ---")
print(f"综合Score: {overall_score}")
print(f"摘要: {summary}")

# 保存解析后的JSON到文件
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")

# ============================================
# 保存到txt文件 (详细日志)
# ============================================
with open(txt_output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("视频分析Report (GUI 任务)\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"Model: {model_name}\n")
    mode_str = "简洁模式 (Concise Mode)"
    f.write(f"Evaluation Mode: {mode_str}\n\n")
    f.write(f"视频文件: {video_file_name}\n")
    f.write(f"文件ID: {video_file.name}\n\n")
    
    f.write(f"I2V提示词:\n{i2v_prompt}\n\n")
    
    if input_image_path and os.path.exists(input_image_path):
        f.write(f"输入图片路径: {input_image_path}\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("发送给 Autorater 的完整 Prompt\n")
    f.write("=" * 50 + "\n")
    f.write(autorater_prompt + "\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("分析结果 (原始JSON文本)\n")
    f.write("=" * 50 + "\n")
    f.write(response.text)

print(f"✓ 详细日志已保存到: {txt_output_filename}")

print("\nScript Execution Completed。")
