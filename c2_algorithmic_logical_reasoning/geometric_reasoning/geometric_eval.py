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
# 获取脚本所在目录，确保路径正确
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
print(f"脚本目录: {SCRIPT_DIR}")
print(f"项目根目录: {PROJECT_ROOT}\n")

# ============================================
# 配置参数
# ============================================
API_KEY = os.environ.get('VLM_API_KEY', '')
task_id = "05"
config_filename = "geometric_eval.json"

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
with open(json_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 提取配置信息
task_config = config[task_id]

# 将JSON中的相对路径与脚本目录合并，生成绝对路径
input_image_path = task_config.get("input_image_path", "")
gt_image_path = task_config.get("gt_image_path", "")
last_frame_image_path = task_config.get("last_frame_image_path", "")
i2v_prompt = task_config.get("i2v_prompt", "N/A")
eval_task_description = task_config["eval_task_description"]

# 基于任务ID创建输出文件名
base_output_name = f"{task_id}_score"

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - 原始图片: {input_image_path}")
print(f"  - 答案图片: {gt_image_path}")
print(f"  - 生成图片: {last_frame_image_path}\n")

# ============================================
# 定义分析prompt - Geometric Reasoning (Image VLM)
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
# 初始化Gemini客户端
# ============================================
client = genai.Client(api_key=API_KEY)

# ============================================
# 辅助函数：上传并等待文件处理
# ============================================
def upload_and_wait(client, file_path, file_desc):
    print(f"正在上传 {file_desc} '{os.path.basename(file_path)}'...")
    file_obj = client.files.upload(file=file_path)
    print(f"  上传成功，文件ID: {file_obj.name}")

    print(f"  等待 {file_desc} 处理...")
    while file_obj.state.name == "PROCESSING":
        time.sleep(2)
        file_obj = client.files.get(name=file_obj.name)
        print(f"    状态: {file_obj.state.name}")
    
    print(f"✓ {file_desc} 文件就绪")
    return file_obj

# ============================================
# 上传所有图片文件（关键步骤）
# ============================================
input_image_file = upload_and_wait(client, input_image_path, "原始图像")
gt_image_file = upload_and_wait(client, gt_image_path, "答案图像")
last_frame_file = upload_and_wait(client, last_frame_image_path, "生成图像")

print("\n✓ 所有图片均已上传并处理完毕，开始分析...\n")

# ============================================
# 调用API生成内容（关键步骤）
# ============================================
model_name = "gemini-2.5-pro"

response = client.models.generate_content(
    model=model_name,
    contents=[
        full_prompt_text,
        "【原始图像】:",
        input_image_file,
        "【答案图像】:",
        gt_image_file,
        "【生成图像】:",
        last_frame_file
    ]
)

# ============================================
# 输出分析结果到终端
# ============================================
print("=" * 50)
print("分析结果")
print("=" * 50)

# 检查响应是否有效
if not hasattr(response, 'text') or not response.text:
    print("❌ API 响应异常！")
    print(f"响应对象: {response}")
    if hasattr(response, 'candidates') and response.candidates:
        print(f"候选结果: {response.candidates}")
    sys.exit(1)

# 准备输出文件路径
output_dir = os.path.join(SCRIPT_DIR, "analysis_results")
if '--output' in sys.argv:
    output_dir = sys.argv[sys.argv.index('--output') + 1]
os.makedirs(output_dir, exist_ok=True)
json_output_filename = os.path.join(output_dir, f"{base_output_name}.json")

# 清理并解析JSON
print(f"\n原始响应长度: {len(response.text)} 字符")
print(f"原始响应前500字符:\n{response.text[:500]}\n")

clean_text = response.text.strip().replace("```json\n", "").replace("```", "")

if not clean_text:
    print("❌ 错误: API 返回为空！")
    print(f"完整响应: {response}")
    sys.exit(1)

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

# 计算归一化分数 (0-1之间)
normalized_score = total_score / criterion_count if criterion_count > 0 else 0

# 将归一化分数添加到结果JSON中
result_json["normalized_score"] = round(normalized_score, 4)
result_json["total_score"] = total_score
result_json["criterion_count"] = criterion_count

print("\n--- Score Summary ---")
print(f"各项Score: {total_score}/{criterion_count}")
print(f"Normalized Score: {normalized_score:.4f} (0-1范围)")
print(f"Percentage Score: {normalized_score * 100:.2f}分")

# 保存解析后的JSON到文件
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")


# ============================================
# 保存到txt文件
# ============================================
output_filename = os.path.join(output_dir, f"{base_output_name}.txt")


# xin==============
# response.usage_metadata 包含详细的 token 计数
usage = response.usage_metadata
print(f"输入 tokens (Prompt): {usage.prompt_token_count}")
print(f"输出 tokens (Response): {usage.candidates_token_count}")
print(f"Total tokens: {usage.total_token_count}")

# 如果使用了缓存,还会有 cached_content_token_count
if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
    print(f"缓存 tokens: {usage.cached_content_token_count}")
# 计算预估成本 (根据 Gemini 2.5 Pro 的定价)
# 注意: 请根据实际定价调整这些值
# Gemini 2.5 Pro 参考价格 (2025):
# 输入: $1.25 / 1M tokens
# 输出: $5.00 / 1M tokens
cost_input = usage.prompt_token_count / 1_000_000 * 1.25
cost_output = usage.candidates_token_count / 1_000_000 * 5.00
total_cost = cost_input + cost_output
print(f"\nEstimated Cost:")
print(f"  输入成本: ${cost_input:.6f}")
print(f"  输出成本: ${cost_output:.6f}")
print(f"  总成本: ${total_cost:.6f} USD")
# xin==============
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("图像分析Report (Geometric Reasoning)\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"Generated Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Task ID: {task_id}\n")
    f.write(f"Model: {model_name}\n")
    mode_str = "简洁模式 (Concise Mode)"
    f.write(f"Evaluation Mode: {mode_str}\n\n")


    # xin==============
    # 添加 Token 统计信息
    f.write("=" * 50 + "\n")
    f.write("Token Usage Statistics\n")
    f.write("=" * 50 + "\n")
    f.write(f"Input tokens: {usage.prompt_token_count}\n")
    f.write(f"Output tokens: {usage.candidates_token_count}\n")
    f.write(f"Total tokens: {usage.total_token_count}\n")
    if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
        f.write(f"缓存 tokens: {usage.cached_content_token_count}\n")
    f.write(f"Estimated Cost: ${total_cost:.6f} USD\n\n")
    # xin==============
    
    f.write(f"I2V Prompt: {i2v_prompt}\n\n")

    f.write(f"原始图像: {input_image_path}\n")
    f.write(f"Answer Image: {gt_image_path}\n")
    f.write(f"Generated Image: {last_frame_image_path}\n\n")
    
    f.write(f"原始图像 (File ID): {input_image_file.name}\n")
    f.write(f"答案图像 (File ID): {gt_image_file.name}\n")
    f.write(f"生成图像 (File ID): {last_frame_file.name}\n\n")

    f.write("=" * 50 + "\n")
    f.write("分析Prompt - Geometric Reasoning 评估\n")
    f.write("=" * 50 + "\n")
    f.write(full_prompt_text + "\n\n")
    
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

print(f"\n✓ 完整Report已保存到: {output_filename}")

# ============================================
# Cleaning uploaded files
# ============================================
print("\n正在Cleaning uploaded files...")
client.files.delete(name=input_image_file.name)
print(f"  ✓ 已删除: {input_image_file.name}")
client.files.delete(name=gt_image_file.name)
print(f"  ✓ 已删除: {gt_image_file.name}")
client.files.delete(name=last_frame_file.name)
print(f"  ✓ 已删除: {last_frame_file.name}")

print("\nScript Execution Completed。")

