#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
batch_extract_last_frame.py - 批量从 2D Rule Extrapolation 视频中提取最后一帧
"""

import cv2
import os
import sys
from pathlib import Path

# ============================================
# 配置区：视频列表
# ============================================
# 使用相对路径：基于当前脚本位置
script_dir = Path(__file__).parent
video_base_dir = str(script_dir / "generated_videos")

video_files = [
    "01_kling_test_01.mp4",
    "02_kling_test_02.mp4",
    "03_kling_test_03.mp4"
]

print("=" * 60)
print("2D Rule Extrapolation 视频批量提取工具")
print("=" * 60)

def extract_last_frame(video_path):
    """提取视频最后一帧"""
    print(f"\n处理: {os.path.basename(video_path)}")
    
    # 检查文件存在
    if not os.path.exists(video_path):
        print(f"  ❌ 文件不存在")
        return False
    
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  ❌ 无法打开视频")
        return False
    
    # 获取信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"  总帧数: {total_frames}, FPS: {fps:.1f}, 分辨率: {width}x{height}")
    
    if total_frames <= 0:
        cap.release()
        print(f"  ❌ 无法获取帧数")
        return False
    
    # 提取最后一帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = cap.read()
    
    if not ret or frame is None:
        # 尝试逐帧读取
        print(f"  ⚠️ 方法1失败，使用方法2...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame = None
        while True:
            ret, temp_frame = cap.read()
            if not ret:
                break
            frame = temp_frame
    
    if frame is None:
        cap.release()
        print(f"  ❌ 无法读取帧")
        return False
    
    # 保存
    output_path = os.path.splitext(video_path)[0] + '.png'
    success = cv2.imwrite(output_path, frame)
    
    cap.release()
    
    if success and os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"  ✓ 成功! 大小: {file_size / 1024:.2f} KB")
        print(f"  保存至: {os.path.basename(output_path)}")
        return True
    else:
        print(f"  ❌ 保存失败")
        return False

# ============================================
# 批量处理
# ============================================
success_count = 0
fail_count = 0

for video_file in video_files:
    video_path = os.path.join(video_base_dir, video_file)
    if extract_last_frame(video_path):
        success_count += 1
    else:
        fail_count += 1

print("\n" + "=" * 60)
print(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
print("=" * 60)

# 列出生成的文件
if success_count > 0:
    print("\n生成的图片文件:")
    for video_file in video_files:
        png_path = os.path.join(video_base_dir, os.path.splitext(video_file)[0] + '.png')
        if os.path.exists(png_path):
            print(f"  ✓ {os.path.basename(png_path)}")

