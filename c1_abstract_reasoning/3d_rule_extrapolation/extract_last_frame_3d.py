#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
extract_last_frame_3d.py - 提取3D规则推理视频的最后一帧
"""

import cv2
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
video_base_dir = os.path.join(SCRIPT_DIR, "generated_videos")
output_dir = os.path.join(video_base_dir, "kling")

os.makedirs(output_dir, exist_ok=True)

video_files = [
    "01_kling_test_01.mp4",
    "02_kling_test_02.mp4",
    "03_kling_test_03.mp4"
]

print("=" * 60)
print("3D规则推理视频提取工具")
print("=" * 60)

def extract_last_frame(video_path, output_path):
    """提取视频最后一帧"""
    print(f"\n处理: {os.path.basename(video_path)}")
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"  总帧数: {total_frames}")
    
    # 提取最后一帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = cap.read()
    
    if not ret or frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame = None
        while True:
            ret, temp_frame = cap.read()
            if not ret:
                break
            frame = temp_frame
    
    cap.release()
    
    success = cv2.imwrite(output_path, frame)
    
    if success:
        print(f"  ✓ 成功! 保存至: {output_path}")
        return True
    else:
        print(f"  ❌ 保存失败")
        return False

# 批量处理
success_count = 0

for video_file in video_files:
    video_path = os.path.join(video_base_dir, video_file)
    output_path = os.path.join(output_dir, os.path.splitext(video_file)[0] + '.png')
    
    if extract_last_frame(video_path, output_path):
        success_count += 1

print("\n" + "=" * 60)
print(f"处理完成: 成功 {success_count}/{len(video_files)}")
print("=" * 60)

