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

# ============================================
# 计时器开始
# ============================================
script_start_time = time.time()

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
API_KEY = "AIzaSyCpHUi8Jf7CTzzMuePUAYfu0uEfBQyKwrY"
task_id = "01"

# ============================================
# 读取配置文件
# ============================================
print(f"正在加载任务: {task_id}...")
config_path = os.path.join(SCRIPT_DIR, "gui_eval_past.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 提取特定任务的配置
if task_id not in config:
    print(f"❌ 错误: 在 'gui.json' 中找不到任务 ID: {task_id}")
    exit(1)

task_config = config[task_id]
autorater_config = task_config["autorater_config"]

# 从配置中动态获取 video_path（将相对路径转换为绝对路径）
video_path_rel = task_config.get("video_path", "path/to/default_video.mp4")
video_path = os.path.join(PROJECT_ROOT, video_path_rel)
video_file_name = os.path.basename(video_path)

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - 视频路径: {video_path}\n")

# ============================================
# 定义分析prompt - 通用模板
# ============================================
autorater_prompt_template = """
You are an expert Video VLM autorater for a GUI (Graphical User Interface) benchmark. 
Your sole task is to watch the provided video and evaluate if it correctly performs the actions specified in the "ORIGINAL_TASK_PROMPT".

**ORIGINAL_TASK_PROMPT:**
{task_prompt}

**EVALUATION CRITERIA (RUBRIC):**
You must evaluate the video by verifying the following steps sequentially. Pay close attention to the *process* of the actions, not just the final result.
{evaluation_rubric}

**REQUIRED OUTPUT FORMAT:**
Provide your evaluation *only* in a valid JSON format. Do not add any text before or after the JSON block. Your entire response must be this JSON object.
{output_json_schema}
"""

# ============================================
# 格式化最终的 Prompt
# ============================================
autorater_prompt = autorater_prompt_template.format(
    task_prompt=autorater_config["original_task_prompt"],
    evaluation_rubric=autorater_config["evaluation_rubric"],
    output_json_schema=autorater_config["output_json_schema"]
)

# ============================================
# 初始化Gemini客户端
# ============================================
print("正在初始化Gemini客户端...")
client = genai.Client(api_key=API_KEY)
model_name = "gemini-2.5-pro"
print(f"✓ Gemini客户端初始化成功, 使用模型: {model_name}\n")

# ============================================
# 上传视频文件
# ============================================
print(f"正在上传视频 '{video_file_name}'...")
if not os.path.exists(video_path):
    print(f"❌ 视频文件未找到: {video_path}")
    exit(1)

upload_start = time.time()
video_file = client.files.upload(file=video_path)
upload_time = time.time() - upload_start
print(f"✓ 上传成功，文件ID: {video_file.name} (耗时: {upload_time:.2f}秒)")

# ============================================
# 等待文件处理完成（关键步骤）
# ============================================
print("等待文件处理...")
processing_start = time.time()
while video_file.state.name == "PROCESSING":
    time.sleep(2)
    video_file = client.files.get(name=video_file.name)
    print(f"  状态: {video_file.state.name}")

if video_file.state.name == "FAILED":
    print("❌ 文件处理失败")
    exit(1)

processing_time = time.time() - processing_start
print(f"✓ 文件就绪，开始分析 (处理耗时: {processing_time:.2f}秒)\n")

# ============================================
# 调用API生成内容
# ============================================
print("正在调用API... (这可能需要一些时间)")
api_start = time.time()
response = client.models.generate_content(
    model=model_name,
    contents=[autorater_prompt, video_file]
)
api_time = time.time() - api_start
print(f"✓ API调用完成 (耗时: {api_time:.2f}秒)\n")

# ============================================
# 输出分析结果到终端
# ============================================
print("=" * 50)
print("分析结果")
print("=" * 50)

# 准备输出文件路径
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_gui")
os.makedirs(output_dir, exist_ok=True)
json_output_filename = os.path.join(output_dir, f"{video_file_name}.json")
txt_output_filename = os.path.join(output_dir, f"{video_file_name}.txt")

# 解析JSON并格式化输出
raw_text = response.text.strip()
clean_text = raw_text.replace("```json", "").replace("```", "").strip()

# 尝试从文本中提取JSON部分
json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
if json_match:
    clean_text = json_match.group(0)

try:
    result_json = json.loads(clean_text)
except json.JSONDecodeError as e:
    print(f"\n❌ JSON解析失败: {e}")
    print(f"错误位置: 第{e.lineno}行, 第{e.colno}列")
    debug_file = os.path.join(output_dir, f"{video_file_name}_debug_raw.txt")
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print(f"原始响应已保存到: {debug_file}")
    print(f"\n原始响应内容预览:")
    print(raw_text[:500] if len(raw_text) > 500 else raw_text)
    exit(1)

print("解析结果 (JSON):")
print(json.dumps(result_json, indent=2, ensure_ascii=False))

# 提取关键信息
overall_score = result_json.get("overall_score", "N/A")
summary = result_json.get("evaluation_summary", "No summary provided.")

print("\n--- 简易摘要 ---")
print(f"综合得分: {overall_score}")
print(f"摘要: {summary}")

# 保存解析后的JSON到文件
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")

# ============================================
# 统计总耗时
# ============================================
total_time = time.time() - script_start_time
print(f"\n{'='*50}")
print("⏱️  耗时统计")
print(f"{'='*50}")
print(f"  上传视频:   {upload_time:.2f}秒")
print(f"  文件处理:   {processing_time:.2f}秒")
print(f"  API调用:    {api_time:.2f}秒")
print(f"  总耗时:     {total_time:.2f}秒")
print(f"{'='*50}\n")

# ============================================
# 保存到txt文件 (详细日志)
# ============================================
with open(txt_output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("视频分析报告 (GUI 任务)\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"任务ID: {task_id}\n")
    f.write(f"使用模型: {model_name}\n")
    f.write(f"视频文件: {video_file_name}\n")
    f.write(f"文件ID: {video_file.name}\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("⏱️  耗时统计\n")
    f.write("=" * 50 + "\n")
    f.write(f"上传视频:   {upload_time:.2f}秒\n")
    f.write(f"文件处理:   {processing_time:.2f}秒\n")
    f.write(f"API调用:    {api_time:.2f}秒\n")
    f.write(f"总耗时:     {total_time:.2f}秒\n\n")
    f.write(f"任务提示 (Original Task Prompt):\n{autorater_config['original_task_prompt']}\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("发送给 Autorater 的完整 Prompt\n")
    f.write("=" * 50 + "\n")
    f.write(autorater_prompt + "\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("分析结果 (原始JSON文本)\n")
    f.write("=" * 50 + "\n")
    f.write(response.text)

print(f"✓ 详细日志已保存到: {txt_output_filename}")

print("\n脚本执行完毕。")