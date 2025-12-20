#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
sudoku_eval.py - Sudoku解题任务评估脚本（使用 Gemini 2.5 Pro - Image VLM）

此脚本评估生成的Sudoku解答图像与标准答案的匹配度。
使用详细解释模式，提供完整的评估理由。
"""

# ============================================
# 导入库
# ============================================
from google import genai
import time
import json
from datetime import datetime
import os
import sys

# ============================================
# 获取脚本所在目录
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"脚本目录: {SCRIPT_DIR}\n")

# ============================================
# 配置参数
# ============================================
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "01"  # 可修改为 "01", "02", "03"
config_filename = "sudoku_eval.json"
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
# 读取配置文件
# ============================================
print("正在读取配置文件...")
json_path = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)

try:
    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ 错误: 找不到配置文件 {json_path}")
    sys.exit(1)

# 提取配置信息
try:
    task_config = config[task_id]
except KeyError:
    print(f"❌ 错误: 在 {json_path} 中找不到Task ID: {task_id}")
    sys.exit(1)

# 将JSON中的相对路径与脚本目录合并
input_image_path = task_config.get("input_image_path", "")
answer_image_path = task_config.get("answer_image_path", "")
last_frame_image_path = task_config.get("last_frame_image_path", "")
i2v_prompt = task_config.get("i2v_prompt", "N/A")
eval_task_description = task_config["eval_task_description"]
max_score = task_config.get("max_score", 9)

# 基于任务ID创建输出文件名
base_output_name = f"{task_id}_score"

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - Input Image: {input_image_path}")
print(f"  - Answer Image: {answer_image_path}")
print(f"  - Generated Image: {last_frame_image_path}")
print(f"  - 总分: {max_score}\n")

# ============================================
# 定义分析 Prompt - Sudoku Evaluation (详细解释版本)
# ============================================

# 添加思考指导
thinking_guidance = """

# EVALUATION PROCESS (Please follow these steps):

Before scoring each criterion, carefully analyze the images:

1. **Examine the Generated Image**
   - Look at each cell in the Sudoku grid
   - Identify which numbers have been filled in
   - Check if numbers are clear and readable

2. **Compare with Ground Truth**
   - Compare the generated solution with the correct answer
   - Check each row for correctness
   - Check each column for correctness
   - Check each 3x3 box for correctness

3. **Verify Sudoku Rules**
   - Each row should contain 1, 2, 3, 4 without repetition
   - Each column should contain 1, 2, 3, 4 without repetition
   - Each 3x3 box should contain 1, 2, 3, 4 without repetition

4. **Assess Stability**
   - Check if original numbers remain unchanged
   - Verify grid structure is intact
   - Look for any visual artifacts or distortions

"""

# 输出格式要求
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

# 组合最终的提示文本
# eval_task_description 已经包含了详细的评分标准
full_prompt_text = eval_task_description + thinking_guidance + output_format_hint

# ============================================
# 初始化 Gemini 客户端
# ============================================
print("正在初始化 Gemini 客户端...")
client = genai.Client(api_key=API_KEY)
print("✓ 客户端初始化成功\n")

# ============================================
# 辅助函数：上传并等待文件处理
# ============================================
def upload_and_wait(client, file_path, file_desc):
    """上传文件并等待其处理完毕"""
    if not os.path.exists(file_path):
        print(f"❌ 错误: 找不到文件 {file_path}")
        return None
    
    print(f"正在上传 {file_desc} '{os.path.basename(file_path)}'...")
    try:
        file_obj = client.files.upload(file=file_path)
        print(f"  上传成功，文件ID: {file_obj.name}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return None
    
    print(f"  等待 {file_desc} 处理...")
    while file_obj.state.name == "PROCESSING":
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)
        print(f"    状态: {file_obj.state.name}")
    
    if file_obj.state.name == "FAILED":
        print(f"❌ {file_desc} 文件处理失败")
        return None
    
    print(f"✓ {file_desc} 文件就绪")
    return file_obj

# ============================================
# 上传所有图片文件
# ============================================
input_image_file = upload_and_wait(client, input_image_path, "输入图像")
answer_image_file = upload_and_wait(client, answer_image_path, "答案图像")
last_frame_file = upload_and_wait(client, last_frame_image_path, "生成图像")

if not all([input_image_file, answer_image_file, last_frame_file]):
    print("❌ 错误: 并非所有图片都上传成功。正在中止。")
    sys.exit(1)

print("\n✓ 所有图片均已上传并处理完毕，开始分析...\n")

# ============================================
# 调用 API 生成内容
# ============================================
print("正在调用 API 进行评估... (这可能需要一些时间)")
try:
    response = client.models.generate_content(
        model=model_name,
        contents=[
            full_prompt_text,
            "【Input Image】 (Original Sudoku Puzzle):",
            input_image_file,
            "【Ground Truth Image】 (Correct Solution):",
            answer_image_file,
            "【Final Frame Image】 (Generated Solution):",
            last_frame_file
        ]
    )
    print("✓ API 调用完成\n")
except Exception as e:
    print(f"❌ API 调用失败: {e}")
    sys.exit(1)

# ============================================
# 输出分析结果到终端
# ============================================
print("=" * 60)
print("Sudoku解题评估结果")
print("=" * 60)

# 准备输出文件路径
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_sudoku")
if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)
json_output_filename = os.path.join(output_dir, f"{base_output_name}.json")

# 清理并解析 JSON
try:
    clean_text = response.text.strip().replace("```json\n", "").replace("```", "")
    result_json = json.loads(clean_text)
except json.JSONDecodeError as e:
    print(f"❌ 错误: 未能解析来自API的JSON响应。")
    print(f"错误详情: {e}")
    print("原始文本:", response.text[:500])
    sys.exit(1)

print("\n解析结果 (JSON):")
print(json.dumps(result_json, indent=2, ensure_ascii=False))

# ============================================
# 计算总分和归一化分数
# ============================================
total_score = 0
criterion_count = 0

for key, value in result_json.items():
    if key.startswith("Criterion_") and isinstance(value, dict):
        score = value.get("score", 0)
        total_score += score
        criterion_count += 1

# 计算归一化分数 (0-1之间)
normalized_score = total_score / max_score if max_score > 0 else 0

# 将归一化分数和任务信息添加到结果JSON中
result_json["total_score"] = total_score
result_json["max_score"] = max_score
result_json["normalized_score"] = round(normalized_score, 4)
result_json["criterion_count"] = criterion_count
result_json["task_id"] = task_id

print("\n" + "=" * 60)
print("Score Summary")
print("=" * 60)
print(f"Total Score: {total_score}/{max_score}")
print(f"Normalized Score: {normalized_score:.4f} (0-1范围)")
print(f"Percentage Score: {normalized_score * 100:.2f}分")

# 显示每个标准的详细评 points
print("\n详细评分:")
for i in range(1, criterion_count + 1):
    criterion_key = f"Criterion_{i}"
    if criterion_key in result_json:
        criterion = result_json[criterion_key]
        print(f"\n  {criterion_key}: {criterion['score']}/3")
        print(f"  Reason: {criterion.get('reason', 'No reason provided')[:100]}...")  # 显示前100个字符

# 保存解析后的JSON到文件
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")

# ============================================
# 保存到 txt 文件
# ============================================
output_filename = os.path.join(output_dir, f"{base_output_name}.txt")

# Token 统计
try:
    usage = response.usage_metadata
    print(f"\n" + "=" * 60)
    print("Token Usage Statistics")
    print("=" * 60)
    print(f"输入 tokens (Prompt): {usage.prompt_token_count}")
    print(f"输出 tokens (Response): {usage.candidates_token_count}")
    print(f"Total tokens: {usage.total_token_count}")
    
    if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
        print(f"缓存 tokens: {usage.cached_content_token_count}")
    
    # 计算预估成本 (Gemini 2.5 Pro 定价)
    cost_input = usage.prompt_token_count / 1_000_000 * 1.25
    cost_output = usage.candidates_token_count / 1_000_000 * 5.00
    total_cost = cost_input + cost_output
    
    print(f"\nEstimated Cost:")
    print(f"  输入成本: ${cost_input:.6f}")
    print(f"  输出成本: ${cost_output:.6f}")
    print(f"  总成本: ${total_cost:.6f} USD")
    print(f"\n注意: 详细解释模式会产生更多输出tokens，")
    print(f"      但提供了更丰富的评估信息。")
except Exception as e:
    print(f"⚠️ 无法计算 token/成本: {e}")
    usage = None
    total_cost = 0.0

# 写入详细Report
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("Sudoku解题Evaluation Report (Sudoku Puzzle Evaluation)\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"Model: {model_name}\n")
    mode_str = "简洁模式 (Concise Mode - Scores Only)"
    f.write(f"Evaluation Mode: {mode_str}\n\n")
    
    # Token 统计信息
    if usage:
        f.write("=" * 60 + "\n")
        f.write("Token Usage Statistics\n")
        f.write("=" * 60 + "\n")
        f.write(f"Input tokens: {usage.prompt_token_count}\n")
        f.write(f"Output tokens: {usage.candidates_token_count}\n")
        f.write(f"Total tokens: {usage.total_token_count}\n")
        if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
            f.write(f"缓存 tokens: {usage.cached_content_token_count}\n")
        f.write(f"Estimated Cost: ${total_cost:.6f} USD\n\n")
        # 现在固定使用简洁模式，无需额外说明
    
    f.write(f"I2V Prompt:\n{i2v_prompt}\n\n")
    
    f.write(f"Input Image: {input_image_path}\n")
    f.write(f"Answer Image: {answer_image_path}\n")
    f.write(f"Generated Image: {last_frame_image_path}\n\n")
    
    f.write(f"输入图像 (File ID): {input_image_file.name}\n")
    f.write(f"答案图像 (File ID): {answer_image_file.name}\n")
    f.write(f"生成图像 (File ID): {last_frame_file.name}\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Score Summary\n")
    f.write("=" * 60 + "\n")
    f.write(f"Total Score: {total_score}/{max_score}\n")
    f.write(f"Normalized Score: {normalized_score:.4f} (0-1范围)\n")
    f.write(f"Percentage Score: {normalized_score * 100:.2f}分\n\n")
    
    # 写入详细的每项评 points
    f.write("=" * 60 + "\n")
    f.write("Detailed Scores and Reasons\n")
    f.write("=" * 60 + "\n\n")
    
    for i in range(1, criterion_count + 1):
        criterion_key = f"Criterion_{i}"
        if criterion_key in result_json:
            criterion = result_json[criterion_key]
            f.write(f"{criterion_key}: Correctness of Solution / Number Range / Environment Stability\n")
            f.write(f"Score: {criterion['score']}/3\n")
            f.write(f"Reason:\n{criterion.get('reason', 'No reason provided')}\n\n")
            f.write("-" * 60 + "\n\n")
    
    f.write("=" * 60 + "\n")
    f.write("Full API Response (原始文本)\n")
    f.write("=" * 60 + "\n")
    f.write(response.text)

print(f"\n✓ 完整Report已保存到: {output_filename}")

# ============================================
# Cleaning uploaded files
# ============================================
print("\n正在Cleaning uploaded files...")
try:
    client.files.delete(name=input_image_file.name)
    print(f"  ✓ 已删除: {input_image_file.name}")
    client.files.delete(name=answer_image_file.name)
    print(f"  ✓ 已删除: {answer_image_file.name}")
    client.files.delete(name=last_frame_file.name)
    print(f"  ✓ 已删除: {last_frame_file.name}")
except Exception as e:
    print(f"  ⚠️ 清理文件时出错 (可能需要手动清理): {e}")

print("\n" + "=" * 60)
print("✓ Script Execution Completed")
print("=" * 60)

