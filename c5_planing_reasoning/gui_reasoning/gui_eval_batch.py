#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================
# 批量评估所有GUI任务的脚本
# ============================================
from google import genai
import time
import json
from datetime import datetime
import os
import sys
import re

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
config_filename = "gui_eval.json"  # 配置文件名

# 命令行参数解析
if '--config' in sys.argv:
    config_filename = sys.argv[sys.argv.index('--config') + 1]

# ============================================
# 读取配置文件
# ============================================
print("正在加载所有任务配置...")
config_path = config_filename if os.path.isabs(config_filename) else os.path.join(SCRIPT_DIR, config_filename)
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

print(f"✓ 已加载 {len(config)} 个任务\n")

# ============================================
# 初始化Gemini客户端
# ============================================
print("正在初始化Gemini客户端...")
client = genai.Client(api_key=API_KEY)
model_name = "gemini-2.5-pro"
print(f"✓ Gemini客户端初始化成功, 使用模型: {model_name}\n")

# 准备输出目录
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_gui")
os.makedirs(output_dir, exist_ok=True)

# 统计信息
total_tasks = len(config)
completed_tasks = 0
failed_tasks = []

# ============================================
# 处理每个任务
# ============================================
for task_id, task_config in config.items():
    print("=" * 70)
    print(f"处理任务 {task_id} ({completed_tasks + 1}/{total_tasks})")
    print("=" * 70)
    
    try:
        # 从配置中动态获取 video_path
        video_path_rel = task_config.get("generated_video_path", "")
        video_path = os.path.join(SCRIPT_DIR, video_path_rel)
        video_file_name = os.path.basename(video_path)
        
        # 提取配置信息
        input_image_path_rel = task_config.get("input_image_path", "")
        input_image_path = os.path.join(SCRIPT_DIR, input_image_path_rel) if input_image_path_rel else None
        i2v_prompt = task_config.get("i2v_prompt", "")
        eval_task_description = task_config.get("eval_task_description", "")
        
        print(f"  - 视频路径: {video_path}")
        if input_image_path:
            print(f"  - 输入图片: {input_image_path}")
        print(f"  - I2V提示词: {i2v_prompt}\n")
        
        # 检查视频文件是否存在
        if not os.path.exists(video_path):
            print(f"❌ 视频文件未找到: {video_path}")
            failed_tasks.append((task_id, "视频文件未找到"))
            continue
        
        # 上传视频文件
        print(f"正在上传视频 '{video_file_name}'...")
        video_file = client.files.upload(file=video_path)
        print(f"✓ 上传成功，文件ID: {video_file.name}")
        
        # 等待文件处理完成
        print("等待文件处理...")
        max_wait_time = 120  # 最多等待2分钟
        wait_time = 0
        while video_file.state.name == "PROCESSING" and wait_time < max_wait_time:
            time.sleep(2)
            wait_time += 2
            video_file = client.files.get(name=video_file.name)
            if wait_time % 10 == 0:
                print(f"  状态: {video_file.state.name} (已等待 {wait_time}s)")
        
        if video_file.state.name == "FAILED":
            print("❌ 文件处理失败")
            failed_tasks.append((task_id, "文件处理失败"))
            continue
        
        if video_file.state.name == "PROCESSING":
            print("❌ 文件处理超时")
            failed_tasks.append((task_id, "文件处理超时"))
            continue
        
        print("✓ 文件就绪，开始分析\n")
        
        # 调用API生成内容
        print("正在调用API...")
        autorater_prompt = eval_task_description
        response = client.models.generate_content(
            model=model_name,
            contents=[autorater_prompt, video_file]
        )
        print("✓ API调用完成\n")
        
        # 清理并解析JSON
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
            debug_file = os.path.join(output_dir, f"{task_id}_{video_file_name}_debug_raw.txt")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(raw_text)
            print(f"原始响应已保存到: {debug_file}")
            failed_tasks.append((task_id, f"JSON解析失败: {str(e)}"))
            continue
        
        # 提取关键信息
        overall_score = result_json.get("overall_score", "N/A")
        summary = result_json.get("evaluation_summary", "No summary provided.")
        
        print("--- 简易摘要 ---")
        print(f"综合得分: {overall_score}")
        print(f"摘要: {summary[:100]}...")
        
        # 保存JSON结果
        json_output_filename = os.path.join(output_dir, f"{task_id}_{video_file_name}.json")
        with open(json_output_filename, "w", encoding="utf-8") as json_file:
            json.dump(result_json, json_file, indent=2, ensure_ascii=False)
        print(f"\n✓ JSON已保存到: {json_output_filename}")
        
        # 保存txt日志
        txt_output_filename = os.path.join(output_dir, f"{task_id}_{video_file_name}.txt")
        with open(txt_output_filename, "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write("视频分析报告 (GUI 任务)\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"任务ID: {task_id}\n")
            f.write(f"使用模型: {model_name}\n")
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
        
        completed_tasks += 1
        
    except Exception as e:
        print(f"\n❌ 任务 {task_id} 处理失败: {str(e)}\n")
        failed_tasks.append((task_id, str(e)))
        continue

# ============================================
# 输出最终统计
# ============================================
print("\n" + "=" * 70)
print("批量处理完成")
print("=" * 70)
print(f"总任务数: {total_tasks}")
print(f"成功完成: {completed_tasks}")
print(f"失败任务: {len(failed_tasks)}")

if failed_tasks:
    print("\n失败的任务列表:")
    for task_id, reason in failed_tasks:
        print(f"  - 任务 {task_id}: {reason}")

# 生成汇总报告
summary_report_path = os.path.join(output_dir, "batch_summary.json")
summary_data = {
    "execution_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "total_tasks": total_tasks,
    "completed_tasks": completed_tasks,
    "failed_tasks": len(failed_tasks),
    "failed_task_details": [{"task_id": tid, "reason": reason} for tid, reason in failed_tasks]
}

with open(summary_report_path, "w", encoding="utf-8") as f:
    json.dump(summary_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ 汇总报告已保存到: {summary_report_path}")
print("\n脚本执行完毕。")

