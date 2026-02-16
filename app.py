import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import random
from collections import deque

# --- ページ設定 ---
st.set_page_config(page_title="Ultimate Maze Generator", layout="centered")

# --- 1. 迷路生成ロジック ---
def generate_maze(width, height):
    if width % 2 == 0: width += 1
    if height % 2 == 0: height += 1
    
    maze = np.ones((height, width), dtype=int)
    
    start_x, start_y = 1, 1
    maze[start_y, start_x] = 0
    stack = [(start_x, start_y)]
    
    while stack:
        x, y = stack[-1]
        directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
        random.shuffle(directions)
        found = False
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and maze[ny, nx] == 1:
                maze[y + dy // 2, x + dx // 2] = 0
                maze[ny, nx] = 0
                stack.append((nx, ny))
                found = True
                break
        if not found:
            stack.pop()
            
    # 上下の壁を開ける
    maze[0, 1] = 0          
    maze[height-1, width-2] = 0 
    
    return maze

# --- 2. 迷路を解くロジック ---
def solve_maze(maze):
    h, w = maze.shape
    start = (1, 1)
    end = (w-2, h-2)
    
    queue = deque([start])
    visited = {start}
    parent = {start: None}
    
    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            break
            
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and maze[ny, nx] == 0 and (nx, ny) not in visited:
                visited.add((nx, ny))
                parent[(nx, ny)] = (x, y)
                queue.append((nx, ny))
    
    path = []
    curr = end
    while curr:
        path.append(curr)
        curr = parent.get(curr)
        
    path.insert(0, (w-2, h-1))
    path.append((1, 0))
        
    return path

# --- 3. 描画ロジック（線の太さ対応） ---
def plot_maze_master(maze, style, hatch=None, roundness=0, sketch_params=None, show_solution=False, solution_width=15):
    h, w = maze.shape
    fig, ax = plt.subplots(figsize=(8, 10))
    
    ax.axis("off")
    ax.set_facecolor('white')
    ax.invert_yaxis()

    # --- 迷路本体 ---
    if style == "標準 (Digital)":
        ax.imshow(maze, cmap="binary", interpolation='nearest')
        ax.
