import cv2
import os

# ============================================
# 配置区：设置输入视频路径
# ============================================
video_path = "algorithm_logic_reasoning/planing_reasoning/GUI/generated_videos/kling/05_kling_test_01.mp4"

# ============================================
# 核心逻辑：提取视频最后一帧
# ============================================

# 1. 打开视频文件
cap = cv2.VideoCapture(video_path)

# 2. 获取视频的总帧数
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# 3. 将读取位置设置到最后一帧（索引是 total_frames - 1）
cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)

# 4. 读取最后一帧的图像数据
ret, frame = cap.read()

# 5. 生成输出路径：将 .mp4 替换为 .png
output_path = os.path.splitext(video_path)[0] + '.png'

# 6. 将图像保存为PNG文件
cv2.imwrite(output_path, frame)

# 7. 释放视频资源
cap.release()

# 输出结果
print(f"✓ 提取完成: {output_path}")

