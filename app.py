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

# --- 【追加】迷路を解くロジック (幅優先探索) ---
def solve_maze(maze):
    h, w = maze.shape
    start = (1, 1)
    end = (w-2, h-2) # 出口の手前
    
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
    
    # パスを復元
    path = []
    curr = end
    while curr:
        path.append(curr)
        curr = parent.get(curr)
        
    # 入り口と出口の外側もパスに追加してあげる（親切設計）
    path.insert(0, (w-2, h-1)) # 出口の外
    path.append((1, 0))        # 入り口の外
        
    return path

# --- 2. 描画ロジック ---
def plot_maze_master(maze, style, hatch=None, roundness=0, sketch_params=None, show_solution=False):
    h, w = maze.shape
    fig, ax = plt.subplots(figsize=(8, 10))
    
    ax.axis("off")
    ax.set_facecolor('white')
    ax.invert_yaxis()

    # --- 迷路の描画 ---
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

    # --- 【追加】正解ルートの描画 ---
    if show_solution:
        path = solve_maze(maze)
        # パス座標をxとyに分解
        px = [p[0] + 0.5 for p in path] # +0.5で道の真ん中に合わせる
        py = [p[1] + 0.5 for p in path]
        
        # 赤い線を引く
        if style == "手書き風 (Sketch)":
             # 手書き風なら線も少し手書きっぽく
             ax.plot(px, py, color="red", linewidth=4, alpha=0.7, 
                     solid_capstyle='round',
                     path_effects=[plt.xkcd()]) 
        else:
            # 通常の線
            ax.plot(px, py, color="red", linewidth=4, alpha=0.7, solid_capstyle='round')

    plt.tight_layout()
    return fig

# --- 3. アプリ画面 (UI) ---
st.title("🧩 Ultimate Maze Generator")

# 設定
st.sidebar.header("設定")
difficulty = st.sidebar.slider("難易度", 5, 25, 13, step=2)

# 【追加】正解を表示するかどうかのチェックボックス
show_solution = st.sidebar.checkbox("✅ 正解ルートを表示する (Answer Key)", value=False)

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
        
        # セッション状態を使って、迷路の形を記憶させると便利だが、
        # まずはシンプルに毎回生成する形にする
        maze_data = generate_maze(width, height)
        
        # 描画関数の呼び出し（正解フラグを渡す）
        fig = plot_maze_master(maze_data, style, hatch_p, round_v, sketch_p, show_solution)
        
        st.pyplot(fig)
        
        # ファイル名の決定
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
