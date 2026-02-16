import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import random

# --- ページ設定 ---
st.set_page_config(page_title="Ultimate Maze Generator", layout="centered")

# --- 1. 迷路生成ロジック（共通） ---
def generate_maze(width, height):
    # 奇数サイズに補正
    if width % 2 == 0: width += 1
    if height % 2 == 0: height += 1
    
    maze = np.ones((height, width), dtype=int)
    
    # 穴掘り法で迷路を作る
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
            
    # 【重要】Canva合成用に上下の壁を強制的に開ける
    maze[0, 1] = 0          # 入り口（上）
    maze[height-1, width-2] = 0 # 出口（下）
    
    return maze

# --- 2. 描画ロジック（スタイル統合版） ---
def plot_maze_master(maze, style, hatch=None, roundness=0, sketch_params=None):
    h, w = maze.shape
    fig, ax = plt.subplots(figsize=(8, 10)) # KDP向け縦長比率
    
    ax.axis("off")
    ax.set_facecolor('white')
    ax.invert_yaxis() # 座標系を反転

    # --- A. 標準（デジタル直線）モード ---
    # 高速描画したい場合のみ使用
    if style == "標準 (Digital)":
        ax.imshow(maze, cmap="binary", interpolation='nearest')
        ax.invert_yaxis() # imshowは反転不要なため戻す
        # imshowだと壁の穴が見えにくくなるため、別途白枠を描画して調整
        # (簡単のため、今回はスタイル適用モードへ流すほうが確実)
    
    # --- B. スタイル適用モード ---
    # 壁をひとつずつ「図形」として描く
    else:
        for y in range(h):
            for x in range(w):
                if maze[y, x] == 1: # 壁の部分
                    
                    # 1. 手書き風 (Sketch)
                    if style == "手書き風 (Sketch)":
                        rect = patches.Rectangle(
                            (x, y), 1, 1, 
                            facecolor="black", edgecolor="black",
                            sketch_params=sketch_params
                        )
                    
                    # 2. テクスチャ/模様 (Pattern)
                    elif style == "模様 (Pattern)":
                        rect = patches.Rectangle(
                            (x, y), 1, 1, 
                            facecolor="white", # 背景白
                            edgecolor="black", # 線は黒
                            hatch=hatch,       # 模様
                            linewidth=0        # 枠線なし
                        )
                    
                    # 3. 角丸 (Rounded)
                    elif style == "角丸 (Rounded)":
                        box_style = f"round,pad=0,rounding_size={roundness}"
                        rect = patches.FancyBboxPatch(
                            (x, y), 1, 1,
                            boxstyle=box_style,
                            facecolor="black", edgecolor="black",
                        )
                    
                    # デフォルト
                    else:
                        rect = patches.Rectangle((x, y), 1, 1, fc="black")
                        
                    ax.add_patch(rect)
        
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)

    plt.tight_layout()
    return fig

# --- 3. アプリ画面 (UI) ---
st.title("🧩 Ultimate Maze Generator")
st.markdown("Canva合成用の穴あき迷路を作成します。")

# === サイドバー設定 ===
st.sidebar.header("設定")

# 難易度
difficulty = st.sidebar.slider("難易度（マスの数）", 5, 25, 13, step=2)

st.sidebar.markdown("---")

# スタイル選択
style = st.sidebar.selectbox(
    "デザインスタイル",
    ["標準 (Digital)", "手書き風 (Sketch)", "模様 (Pattern)", "角丸 (Rounded)"]
)

# スタイルごとの詳細設定
hatch_p = None
round_v = 0
sketch_p = None

if style == "手書き風 (Sketch)":
    st.sidebar.caption("手書きのヨレ具合を調整")
    scale = st.sidebar.slider("ヨレ (Scale)", 1.0, 10.0, 3.0)
    length = st.sidebar.slider("細かさ (Length)", 10.0, 150.0, 100.0)
    sketch_p = {'scale': scale, 'length': length, 'randomness': 10.0}

elif style == "模様 (Pattern)":
    pat_type = st.sidebar.selectbox("模様の種類", ["斜線 (///)", "ドット (...)", "クロス (xx)", "星 (**)"])
    if "斜線" in pat_type: hatch_p = "///"
    elif "ドット" in pat_type: hatch_p = ".."
    elif "クロス" in pat_type: hatch_p = "xx"
    elif "星" in pat_type: hatch_p = "**"

elif style == "角丸 (Rounded)":
    round_v = st.sidebar.slider("丸みの強さ", 0.1, 1.0, 0.4)

# === メインエリア ===
if st.button("迷路を生成する"):
    with st.spinner("描画中..."):
        # サイズ計算（縦長レターサイズ比率 1:1.3）
        width = difficulty
        height = int(width * 1.3)
        
        # 処理
        maze_data = generate_maze(width, height)
        fig = plot_maze_master(maze_data, style, hatch_p, round_v, sketch_p)
        
        st.pyplot(fig)
        
        # 保存
        buf = BytesIO()
        fig.savefig(buf, format="pdf", dpi=300, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        
        st.download_button(
            label="📄 PDFダウンロード",
            data=buf,
            file_name=f"maze_{style}.pdf",
            mime="application/pdf"
        )
