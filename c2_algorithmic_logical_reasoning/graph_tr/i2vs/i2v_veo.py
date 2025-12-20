# ============================================
# 导入库
# ============================================
import time
import base64
from google import genai
from google.genai import types
model_name = "veo-3.0-generate-001" #"veo-3.0-fast-generate-001"
# ============================================
# 初始化客户端
# ============================================
client = genai.Client(api_key="AIzaSyCpHUi8Jf7CTzzMuePUAYfu0uEfBQyKwrY")

# ============================================
# 定义输入图片和prompt
# ============================================
input_image_path = "algorithm_logic_reasoning/math_logic/graph_tr/input_images_green/03.png"  # 从工作目录出发的相对路径

prompt = """Starting from the blue well, an unlimited supply of blue water moves through the connected channel system without spilling into the white area. """

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
output_filename = f"veo3_graph_flow_no_audio_{time_stamp}.mp4"

client.files.download(file=video.video)
video.video.save(output_filename)

print(f"✓ 视频已保存到: {output_filename}")
print("💰 提示: 使用无音频模式预计节省约33%的费用")