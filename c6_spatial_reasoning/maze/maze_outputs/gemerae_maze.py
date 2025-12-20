"""
生成迷宫数据集并保存为图片
- 每个迷宫生成两张图片：迷宫本身 和 带解决方案的迷宫
"""

from maze_dataset import MazeDataset, MazeDatasetConfig
from maze_dataset.generation import LatticeMazeGenerators
import matplotlib.pyplot as plt
import numpy as np
import os

def create_output_directory(dir_name="maze_outputs"):
    """创建输出目录"""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

def generate_maze_images(n_mazes=5, grid_size=10, output_dir="maze_outputs"):
    """
    生成迷宫并保存图片
    
    参数:
        n_mazes: 生成迷宫的数量
        grid_size: 迷宫的大小（grid_size x grid_size）
        output_dir: 输出目录
    """
    
    # 创建输出目录
    output_dir = create_output_directory(output_dir)
    
    # 配置迷宫数据集
    print(f"正在生成 {n_mazes} 个 {grid_size}x{grid_size} 的迷宫...")
    cfg = MazeDatasetConfig(
        name="my_mazes",
        grid_n=grid_size,  # 迷宫大小
        n_mazes=n_mazes,   # 迷宫数量
        maze_ctor=LatticeMazeGenerators.gen_dfs,  # 使用深度优先搜索算法
        maze_ctor_kwargs=dict(do_forks=True),  # 允许分叉
    )
    
    # 生成数据集
    dataset = MazeDataset.from_config(cfg)
    print(f"成功生成 {len(dataset)} 个迷宫！\n")
    
    # 为每个迷宫生成两张图片
    for i, maze in enumerate(dataset):
        print(f"处理迷宫 {i+1}/{n_mazes}...")
        
        # 获取迷宫的像素表示
        # as_pixels() 方法有参数: show_endpoints, show_solution
        
        # 1. 生成只有迷宫的图片（不显示解决方案，但要标记起点和终点）
        maze_only = maze.as_pixels(show_endpoints=False, show_solution=False).copy()
        
        # 手动标记起点和终点（缩小标记大小，并确保在通道上）
        # 获取起点和终点坐标
        start_pos = maze.start_pos
        end_pos = maze.end_pos
        
        # 计算像素缩放比例
        pixel_scale = maze_only.shape[0] // grid_size
        
        # 每个单元格的中心位置（通道在中心，墙壁在边缘）
        cell_center_offset = pixel_scale // 2
        
        # 计算标记大小（缩小一些）
        marker_size = max(pixel_scale // 3, 1)
        marker_half = marker_size // 2
        
        # 标记起点为绿色（在单元格中心的小方块）
        start_center_row = start_pos[0] * pixel_scale + cell_center_offset
        start_center_col = start_pos[1] * pixel_scale + cell_center_offset
        start_row = start_center_row - marker_half
        start_col = start_center_col - marker_half
        end_start_row = min(start_row + marker_size, maze_only.shape[0])
        end_start_col = min(start_col + marker_size, maze_only.shape[1])
        maze_only[start_row:end_start_row, start_col:end_start_col] = [0, 255, 0]  # 绿色起点
        
        # 标记终点为红色（在单元格中心的小方块）
        end_center_row = end_pos[0] * pixel_scale + cell_center_offset
        end_center_col = end_pos[1] * pixel_scale + cell_center_offset
        end_row = end_center_row - marker_half
        end_col = end_center_col - marker_half
        end_end_row = min(end_row + marker_size, maze_only.shape[0])
        end_end_col = min(end_col + marker_size, maze_only.shape[1])
        maze_only[end_row:end_end_row, end_col:end_end_col] = [255, 0, 0]  # 红色终点
        
        # 2. 生成带解决方案的图片
        maze_with_solution = maze.as_pixels(show_endpoints=True, show_solution=True)
        
        # 保存迷宫图片（不含解）
        plt.figure(figsize=(8, 8))
        plt.imshow(maze_only)
        plt.axis('off')
        plt.title(f'Maze {i+1} (No Solution)', fontsize=16, pad=20)
        maze_only_path = os.path.join(output_dir, f'maze_{i+1}_only.png')
        plt.savefig(maze_only_path, bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  ✓ 保存迷宫图片: {maze_only_path}")
        
        # 保存带解决方案的图片
        plt.figure(figsize=(8, 8))
        plt.imshow(maze_with_solution)
        plt.axis('off')
        plt.title(f'Maze {i+1} (With Solution)', fontsize=16, pad=20)
        maze_solution_path = os.path.join(output_dir, f'maze_{i+1}_solution.png')
        plt.savefig(maze_solution_path, bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  ✓ 保存解决方案图片: {maze_solution_path}")
        
        # 打印迷宫信息
        print(f"  - 迷宫大小: {grid_size}x{grid_size}")
        print(f"  - 解决方案长度: {len(maze.solution)} 步\n")
    
    print(f"完成！所有图片已保存到 '{output_dir}' 目录")
    return output_dir

def display_ascii_preview(dataset, n=1):
    """
    在控制台显示迷宫的 ASCII 预览
    
    参数:
        dataset: 迷宫数据集
        n: 显示前 n 个迷宫
    """
    print("\n" + "="*60)
    print("ASCII 预览:")
    print("="*60)
    for i in range(min(n, len(dataset))):
        print(f"\n迷宫 {i+1}:")
        print(dataset[i].as_ascii())
    print("="*60 + "\n")

if __name__ == "__main__":
    # 配置参数
    NUM_MAZES = 5      # 生成5个迷宫
    GRID_SIZE = 6     # 10x10 的迷宫大小（可以调整）
    OUTPUT_DIR = f"maze_outputs/{GRID_SIZE}x{GRID_SIZE}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("="*60)
    print("迷宫生成器")
    print("="*60)
    
    # 生成迷宫并保存图片
    output_dir = generate_maze_images(
        n_mazes=NUM_MAZES,
        grid_size=GRID_SIZE,
        output_dir=OUTPUT_DIR
    )
    
    # 重新加载数据集用于预览
    cfg = MazeDatasetConfig(
        name="my_mazes",
        grid_n=GRID_SIZE,
        n_mazes=NUM_MAZES,
        maze_ctor=LatticeMazeGenerators.gen_dfs,
        maze_ctor_kwargs=dict(do_forks=True),
    )
    dataset = MazeDataset.from_config(cfg)
    
    # 显示第一个迷宫的 ASCII 预览
    display_ascii_preview(dataset, n=1)
    
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"📊 生成文件数: {NUM_MAZES * 2} 张图片")