# ============================================
# 导入库
# ============================================
import time
import base64
import json
import os
from google import genai
from google.genai import types

# ============================================
# 配置参数
# ============================================
model_name = "veo-3.0-generate-001"  # "veo-3.0-fast-generate-001"
task_id = "02"  # 可选: "01"(椅子), "02"(桌子), "03"(书架)

# ============================================
# 初始化客户端
# ============================================
client = genai.Client(api_key="AIzaSyCpHUi8Jf7CTzzMuePUAYfu0uEfBQyKwrY")

# ============================================
# 读取配置文件
# ============================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
prompt_json_path = os.path.join(PROJECT_ROOT, "prompt.json")

print(f"正在读取配置文件: {prompt_json_path}")
with open(prompt_json_path, "r", encoding="utf-8") as f:
    config = json.load(f)

task_config = config[task_id]
prompt = task_config["prompt"]
task_name = task_config.get("name", f"任务{task_id}")

print(f"✓ 已加载任务: {task_id} - {task_name}\n")

# ============================================
# 定义输入图片
# ============================================
input_image_path = "algorithm_logic_reasoning/planing_reasoning/assemble/input_images/image.png"
# ============================================
# 读取本地图片并转为base64
# ============================================
print(f"正在读取图片 '{input_image_path}'...")
with open(input_image_path, "rb") as image_file:
    image_bytes = image_file.read()

# 将图片转换为base64编码
image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# 创建符合API要求的图片对象
input_image = types.Image(
    image_bytes=image_bytes,
    mime_type="image/png"
)
print("✓ 图片读取成功\n")

# ============================================
# 使用Veo 3 生成视频（无音频）
# ============================================
print("开始生成视频（使用 Veo 3,无音频）...")
operation = client.models.generate_videos(
    model=model_name,  # ✅ 改为 Veo 3 稳定版
    prompt=prompt,
    image=input_image,
    config=types.GenerateVideosConfig(
        resolution="720p",
        duration_seconds=8,
        aspect_ratio="16:9",
    )
)

# ============================================
# 轮询等待视频生成完成
# ============================================
print("视频生成中,这可能需要几分钟时间...")
while not operation.done:
    print("⏳ 等待视频生成中...")
    time.sleep(10)  # 每10秒检查一次
    operation = client.operations.get(operation)

print("✓ 视频生成完成\n")

# ============================================
# 下载并保存视频
# ============================================
time_stamp = time.strftime("%Y%m%d_%H%M%S")
video = operation.response.generated_videos[0]
output_dir = os.path.join(PROJECT_ROOT, "generated_videos")
os.makedirs(output_dir, exist_ok=True)
output_filename = os.path.join(output_dir, f"{task_id}_veo_test_01.mp4")

client.files.download(file=video.video)
video.video.save(output_filename)

print(f"✓ 视频已保存到: {output_filename}")
print(f"任务: {task_id} - {task_name}")
print("💰 提示: 使用无音频模式预计节省约33%的费用")