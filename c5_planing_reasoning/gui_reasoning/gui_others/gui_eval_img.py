# ============================================
# 导入库
# ============================================
from google import genai
import time
import json
from datetime import datetime
import os

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
API_KEY = "AIzaSyCpHUi8Jf7CTzzMuePUAYfu0uEfBQyKwrY"
task_id = "05"

# ============================================
# 读取配置文件
# ============================================
print("正在读取配置文件...")
json_path = os.path.join(SCRIPT_DIR, "gui_img.json")
with open(json_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# 提取配置信息
task_config = config[task_id]

# 将JSON中的相对路径与脚本目录合并，生成绝对路径
input_image_path = os.path.join(SCRIPT_DIR, task_config["input_image_path"])
gt_image_path = os.path.join(SCRIPT_DIR, task_config["gt_image_path"])
last_frame_image_path = os.path.join(SCRIPT_DIR, task_config["last_frame_image_path"])
i2v_prompt = task_config.get("i2v_prompt", "N/A")
eval_task_description = task_config["eval_task_description"]

# 基于最后帧的文件名，创建用于输出的
base_output_name = os.path.basename(last_frame_image_path)

print(f"✓ 已加载任务配置: {task_id}")
print(f"  - 原始图片: {input_image_path}")
print(f"  - 答案图片: {gt_image_path}")
print(f"  - 生成图片: {last_frame_image_path}\n")

# ============================================
# 定义分析prompt - GUI Image Evaluation
# ============================================
# 这是一个通用的系统提示，它将与来自JSON的任务描述结合使用
system_prompt_for_autorater = f"""
<system>
# 角色：GUI推理基准自动评分员 (Autorater)

你是一个用于评估GUI（图形用户界面）任务的自动评分系统。你的任务是比较视频生成模型的输出（【生成图像】，即最后一帧）和一个"正确答案"参考图（【答案图像】）。

【答案图像】上可能会使用红色标注框来指明必须被正确生成的关键区域 (Regions of Interest, ROIs)。

# 你的任务：

你将收到：
1. **【原始图像】(Input Image)**：任务开始前的初始状态图像。
2. **【答案图像】(Ground Truth Image)**：带有红色标注框 (ROIs) 的参考图像，显示正确完成任务后的状态。
3. **【生成图像】(Generated Image)**：由视频模型生成的最后一帧图像。

你的目标是根据任务描述中的评估标准逐一评估【生成图像】，并以JSON格式输出你的评分和理由。

# 重要说明：

- 【答案图像】上的红色标注框仅用于指明关键区域，不是实际内容的一部分。
- 你需要比较【生成图像】与【答案图像】的实际内容，而不是标注框本身。
- 严格按照任务描述中的评估标准和输出格式进行评估。

</system>
"""

# 将系统提示和具体的任务描述组合成最终的文本提示
full_prompt_text = system_prompt_for_autorater + "\n\n" + eval_task_description

# ============================================
# 初始化Gemini客户端
# ============================================
client = genai.Client(api_key=API_KEY)

# ============================================
# 辅助函数：上传并等待文件处理
# ============================================
def upload_and_wait(client, file_path, file_desc):
    """上传文件并等待其处理完毕"""
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
        "【原始图像】(Input Image):",
        input_image_file,
        "【答案图像】(Ground Truth Image):",
        gt_image_file,
        "【生成图像】(Generated Image):",
        last_frame_file
    ]
)

# ============================================
# 输出分析结果到终端
# ============================================
print("=" * 50)
print("GUI图像分析结果")
print("=" * 50)

# 准备输出文件路径
output_dir = os.path.join(SCRIPT_DIR, "analysis_results_gui_img")
os.makedirs(output_dir, exist_ok=True)
json_output_filename = os.path.join(output_dir, f"{base_output_name}.json")

# 清理并解析JSON
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

# 计算归一化分数 (0-1之间)
normalized_score = total_score / criterion_count if criterion_count > 0 else 0

# 将归一化分数添加到结果JSON中
result_json["normalized_score"] = round(normalized_score, 4)
result_json["total_score"] = total_score
result_json["criterion_count"] = criterion_count

print("\n--- 评分摘要 ---")
print(f"各项得分: {total_score}/{criterion_count}")
print(f"归一化分数: {normalized_score:.4f} (0-1范围)")
print(f"百分制分数: {normalized_score * 100:.2f}分")

# 保存解析后的JSON到文件
with open(json_output_filename, "w", encoding="utf-8") as json_file:
    json.dump(result_json, json_file, indent=2, ensure_ascii=False)
print(f"\n✓ JSON已保存到: {json_output_filename}")


# ============================================
# 保存到txt文件
# ============================================
output_filename = os.path.join(output_dir, f"{base_output_name}.txt")


# Token统计
usage = response.usage_metadata
print(f"\n输入 tokens (Prompt): {usage.prompt_token_count}")
print(f"输出 tokens (Response): {usage.candidates_token_count}")
print(f"总计 tokens: {usage.total_token_count}")

# 如果使用了缓存
if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
    print(f"缓存 tokens: {usage.cached_content_token_count}")

# 计算预估成本
# Gemini 2.5 Pro 参考价格 (2025):
# 输入: $1.25 / 1M tokens
# 输出: $5.00 / 1M tokens
cost_input = usage.prompt_token_count / 1_000_000 * 1.25
cost_output = usage.candidates_token_count / 1_000_000 * 5.00
total_cost = cost_input + cost_output
print(f"\n预估成本:")
print(f"  输入成本: ${cost_input:.6f}")
print(f"  输出成本: ${cost_output:.6f}")
print(f"  总成本: ${total_cost:.6f} USD")

with open(output_filename, "w", encoding="utf-8") as f:
    f.write("=" * 50 + "\n")
    f.write("GUI图像分析报告\n")
    f.write("=" * 50 + "\n\n")
    
    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"任务ID: {task_id}\n")
    f.write(f"使用模型: {model_name}\n\n")

    # Token统计信息
    f.write("=" * 50 + "\n")
    f.write("Token 使用统计\n")
    f.write("=" * 50 + "\n")
    f.write(f"输入 tokens: {usage.prompt_token_count}\n")
    f.write(f"输出 tokens: {usage.candidates_token_count}\n")
    f.write(f"总计 tokens: {usage.total_token_count}\n")
    if hasattr(usage, 'cached_content_token_count') and usage.cached_content_token_count:
        f.write(f"缓存 tokens: {usage.cached_content_token_count}\n")
    f.write(f"预估成本: ${total_cost:.6f} USD\n\n")
    
    f.write(f"I2V Prompt: {i2v_prompt}\n\n")

    f.write(f"原始图像: {input_image_path}\n")
    f.write(f"答案图像: {gt_image_path}\n")
    f.write(f"生成图像: {last_frame_image_path}\n\n")
    
    f.write(f"原始图像 (File ID): {input_image_file.name}\n")
    f.write(f"答案图像 (File ID): {gt_image_file.name}\n")
    f.write(f"生成图像 (File ID): {last_frame_file.name}\n\n")

    f.write("=" * 50 + "\n")
    f.write("分析Prompt - GUI图像评估\n")
    f.write("=" * 50 + "\n")
    f.write(full_prompt_text + "\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("评分摘要\n")
    f.write("=" * 50 + "\n")
    f.write(f"各项得分: {total_score}/{criterion_count}\n")
    f.write(f"归一化分数: {normalized_score:.4f} (0-1范围)\n")
    f.write(f"百分制分数: {normalized_score * 100:.2f}分\n\n")
    
    f.write("=" * 50 + "\n")
    f.write("分析结果 (原始文本)\n")
    f.write("=" * 50 + "\n")
    f.write(response.text)

print(f"\n✓ 完整报告已保存到: {output_filename}")

# ============================================
# 清理上传的文件
# ============================================
print("\n正在清理上传的文件...")
client.files.delete(name=input_image_file.name)
print(f"  ✓ 已删除: {input_image_file.name}")
client.files.delete(name=gt_image_file.name)
print(f"  ✓ 已删除: {gt_image_file.name}")
client.files.delete(name=last_frame_file.name)
print(f"  ✓ 已删除: {last_frame_file.name}")

print("\n脚本执行完毕。")
