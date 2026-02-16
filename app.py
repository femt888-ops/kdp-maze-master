import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import random
from collections import deque

# --- ページ設定 ---
st.set_page_config(page_title="Ultimate Maze Generator", layout="centered")

# --- 1. 迷路生成ロジック（登山モード：下から上へ） ---
def generate_maze(width, height):
    if width % 2 == 0: width += 1
    if height % 2 == 0: height += 1
    
    maze = np.ones((height, width), dtype=int)
    
    # 【ここが重要】スタート地点を「左下」にする
    # height-2 が一番下の道
    start_x, start_y = 1, height - 2
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
            
    # 【穴の位置を変更】
    # スタート穴：左下（height-1, 1）
    maze[height-1, 1] = 0          
    
    # ゴール穴：右上（0, width-2）
    maze[0, width-2] = 0 
    
    return maze

# --- 2. 迷路を解くロジック ---
def solve_maze(maze):
    h, w = maze.shape
    
    # スタート：左下
    start = (1, h - 2)
    # ゴール：右上
    end = (w - 2, 1)
    
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
        
    # パスを外側に延長
    path.insert(0, (w-2, 0))      # ゴールの外（上へ抜ける）
    path.append((1, h-1))         # スタートの外（下から入る）
        
    return path

# --- 3. 描画ロジック ---
def plot_maze_master(maze, style, hatch=None, roundness=0, sketch_params=None, show_solution=False, solution_width=15):
    h, w = maze.shape
    fig, ax = plt.subplots(figsize=(8, 10))
    
    ax.axis("off")
    ax.set_facecolor('white')
    ax.invert_yaxis() 

    # --- 迷路本体 ---
    if style == "標準 (Digital)":
        ax.imshow(maze, cmap="binary", interpolation='nearest')
        ax.invert_yaxis()
    else:
        for y in range(h):
            for x in range(w):
                if maze[y, x] == 1: # 壁
                    if style == "手書き風 (Sketch)":
                        rect = patches.Rectangle(
                            (x, y), 1, 1, 
                            facecolor="black", edgecolor="black"
                        )
                        if sketch_params: rect.set_sketch_params(**sketch_params)
                    elif style == "模様 (Pattern)":
                        rect = patches.Rectangle(
                            (x, y), 1, 1, 
                            facecolor="white", edgecolor="black", 
                            hatch=hatch, linewidth=0
                        )
                    elif style == "角丸 (Rounded)":
                        box_style = f"round,pad=0,rounding_size={roundness}"
                        rect = patches.FancyBboxPatch(
                            (x, y), 1, 1,
                            boxstyle=box_style,
                            facecolor="black", edgecolor="black",
                        )
                    else:
                        rect = patches.Rectangle((x, y), 1, 1, fc="black")
                    ax.add_patch(rect)
        
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)

    # --- 正解ルート & マーカー ---
    if show_solution:
        path = solve_maze(maze)
        px = [p[0] + 0.5 for p in path]
        py = [p[1] + 0.5 for p in path]
        
        # 線を引く
        if style == "手書き風 (Sketch)":
             with plt.xkcd():
                 ax.plot(px, py, color="red", linewidth=solution_width, solid_capstyle='round', zorder=10)
        else:
            ax.plot(px, py, color="red", linewidth=solution_width, solid_capstyle='round', zorder=10)
            
        marker_size = solution_width * 1.5 
        
        # スタート（左下）：丸 (o)
        ax.plot(px[-1], py[-1], marker='o', color="red", markersize=marker_size, zorder=11, clip_on=False)

        # ゴール（右上）：上向き矢印 (^)
        ax.plot(px[0], py[0], marker='^', color="red", markersize=marker_size*1.3, zorder=11, clip_on=False)

    plt.tight_layout()
    return fig

# --- 4. アプリUI ---
st.title("🧩 Ultimate Maze (Climbing Mode)")
st.caption("下（スタート）から上（ゴール）を目指す登山モード")

st.sidebar.header("設定")
difficulty = st.sidebar.slider("難易度", 5, 25, 13, step=2)

st.sidebar.markdown("---")
# チェックボックス
show_solution = st.sidebar.checkbox("✅ 正解ルートを表示 (Answer Key)", value=False)

sol_width = 15 
if show_solution:
    sol_width = st.sidebar.slider("🖍️ 正解の線の太さ", 1, 40, 15)

st.sidebar.markdown("---")

style = st.sidebar.selectbox(
    "デザインスタイル",
    ["標準 (Digital)", "手書き風 (Sketch)", "模様 (Pattern)", "角丸 (Rounded)"]
)

hatch_p = None
round_v = 0
sketch_p = None

if style == "手書き風 (Sketch)":
    scale = st.sidebar.slider("ヨレ (Scale)", 1.0, 10.0, 3.0)
    length = st.sidebar.slider("細かさ (Length)", 10.0, 150.0, 100.0)
    sketch_p = {'scale': scale, 'length': length, 'randomness': 10.0}

elif style == "模様 (Pattern)":
    pat_type = st.sidebar.selectbox("模様", ["斜線 (///)", "ドット (...)", "クロス (xx)", "星 (**)"])
    if "斜線" in pat_type: hatch_p = "///"
    elif "ドット" in pat_type: hatch_p = ".."
    elif "クロス" in pat_type: hatch_p = "xx"
    elif "星" in pat_type: hatch_p = "**"

elif style == "角丸 (Rounded)":
    round_v = st.sidebar.slider("丸み", 0.1, 1.0, 0.4)

# 生成ボタン
if st.button("迷路を生成する"):
    with st.spinner("描画中..."):
        width = difficulty
        height = int(width * 1.3)
        
        maze_data = generate_maze(width, height)
        fig = plot_maze_master(maze_data, style, hatch_p, round_v, sketch_p, show_solution, sol_width)
        
        st.pyplot(fig)
        
        file_prefix = "solution" if show_solution else "maze"
        
        buf = BytesIO()
        fig.savefig(buf, format="pdf", dpi=300, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        
        st.download_button(
            label="📄 PDFダウンロード",
            data=buf,
            file_name=f"{file_prefix}_{style}.pdf",
            mime="application/pdf"
        )
