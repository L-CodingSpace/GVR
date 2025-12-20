import cv2
import os

# ============================================
# 配置区：设置输入视频路径
# ============================================
video_path = "algorithm_logic_reasoning/abstract_reasoning/symmetry/generated_videos/random_03.mp4"

# ============================================
# 核心逻辑：提取视频最后一帧并生成下半部分
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
output_path_full = os.path.splitext(video_path)[0] + '.png'

# 6. 保存完整的最后一帧
cv2.imwrite(output_path_full, frame)
print(f"✓ 完整帧已保存: {output_path_full}")

# 7. 裁剪下半部分
height, width = frame.shape[:2]
half_frame = frame[height // 2:, :]  # 从中间到底部

# 8. 生成下半部分输出路径
output_path_half = os.path.splitext(video_path)[0] + '_half.png'

# 9. 保存下半部分
cv2.imwrite(output_path_half, half_frame)
print(f"✓ 下半部分已保存: {output_path_half}")
print(f"  原始尺寸: {width} x {height}")
print(f"  裁剪尺寸: {width} x {height // 2}")

# 10. 释放视频资源
cap.release()

