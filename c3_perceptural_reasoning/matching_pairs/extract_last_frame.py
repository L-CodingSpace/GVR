import cv2
import os
import glob

# ============================================
# 批量提取视频最后一帧
# ============================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
video_dir = os.path.join(SCRIPT_DIR, "generated_videos")

video_files = glob.glob(os.path.join(video_dir, "*.mp4"))

print(f"找到 {len(video_files)} 个视频文件")

for video_path in video_files:
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = cap.read()
    
    output_path = os.path.splitext(video_path)[0] + '.png'
    cv2.imwrite(output_path, frame)
    cap.release()
    
    print(f"✓ 提取完成: {os.path.basename(output_path)}")

print(f"\n完成！共提取 {len(video_files)} 个最后帧")

