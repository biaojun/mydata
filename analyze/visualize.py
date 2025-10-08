"""任务级与全局可视化。

依赖：
- matplotlib（函数内按需导入）
- wordcloud（仅词云函数需要；函数内按需导入）
 未安装时会抛出 ImportError，请先安装：pip install matplotlib
  词云：pip install wordcloud pillow
"""

from __future__ import annotations


def plot_task_dimension_lollipop(task_json_path: str, out_path: str) -> str:
    """为单个任务绘制维度棒棒糖/误差线图。

    输入文件可以是：
    - 单个任务的 JSON 对象；
    - JSONL（多任务），则默认取首条记录。
    """
    import json
    import os
    from .schemas import Dimension

    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 matplotlib，安装：pip install matplotlib") from e

    # 读取单个任务对象
    with open(task_json_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        obj = None
        if content.startswith("{") and content.endswith("}"):
            obj = json.loads(content)
        else:
            # JSONL：取第一行
            line = content.splitlines()[0]
            obj = json.loads(line)

    dim_agg = (obj.get("task_level_agg") or {}).get("dimension_agg") or {}
    dims = [d.value for d in Dimension]

    means = [float((dim_agg.get(d) or {}).get("mean_delta", 0.0)) for d in dims]
    meds = [float((dim_agg.get(d) or {}).get("median_delta", 0.0)) for d in dims]
    mins = [float((dim_agg.get(d) or {}).get("min_delta", 0.0)) for d in dims]
    maxs = [float((dim_agg.get(d) or {}).get("max_delta", 0.0)) for d in dims]

    y = list(range(len(dims)))

    plt.figure(figsize=(10, 6))
    # 误差线（min-max）
    for i, (mn, mx) in enumerate(zip(mins, maxs)):
        plt.plot([mn, mx], [i, i], color="#888", linewidth=2, zorder=1)
    # 点：min / median / mean / max
    plt.scatter(mins, y, label="min", color="#d62728", zorder=2)
    plt.scatter(meds, y, label="median", color="#1f77b4", zorder=3)
    plt.scatter(means, y, label="mean", color="#2ca02c", zorder=4)
    plt.scatter(maxs, y, label="max", color="#ff7f0e", zorder=5)

    plt.yticks(y, dims, fontsize=9)
    plt.xlabel("Score Delta (Good - Bad)")
    plt.title("Code Quality Gap Analysis: Good vs Bad Code")
    plt.grid(axis="x", linestyle=":", alpha=0.5)
    plt.legend(loc="lower right")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_task_keywords_bar(task_json_path: str, out_path: str) -> str:
    """绘制任务级 Top-K 区分性关键词条形图。

    默认取 Top-20（按权重和排序）。
    """
    import json
    import os

    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 matplotlib，安装：pip install matplotlib") from e

    with open(task_json_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        obj = None
        if content.startswith("{") and content.endswith("}"):
            obj = json.loads(content)
        else:
            line = content.splitlines()[0]
            obj = json.loads(line)

    kws = (obj.get("task_level_agg") or {}).get("aggregated_keywords") or []
    # 规范字段名（可能是对象列表或已为 dict）
    items = [
        {
            "phrase": str(k.get("phrase", "")),
            "weight": float(k.get("weight", k.get("weight_sum", 0.0))),
            "dimension": str(k.get("dimension", "")),
        }
        for k in kws
    ]
    items.sort(key=lambda r: r["weight"], reverse=True)
    items = items[:20]

    phrases = [f"{it['phrase']} ({it['dimension']})" for it in items]
    weights = [it["weight"] for it in items]

    plt.figure(figsize=(10, max(4, len(items) * 0.4)))
    y = list(range(len(items)))
    plt.barh(y, weights, color="#1f77b4")
    plt.yticks(y, phrases, fontsize=8)
    plt.xlabel("Weight")
    plt.title("Key Differences: Good vs Bad Code (Top-20)")
    plt.gca().invert_yaxis()
    plt.grid(axis="x", linestyle=":", alpha=0.5)
    import os as _os
    _os.makedirs(_os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_global_radar(agg_dimension_csv: str, out_path: str) -> str:
    """绘制九维全局雷达图（使用 mean_mean_delta）。"""
    import csv
    import math
    import os
    from .schemas import Dimension

    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 matplotlib，安装：pip install matplotlib") from e

    rows = []
    with open(agg_dimension_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    dims = [d.value for d in Dimension]
    values = []
    for d in dims:
        r = next((x for x in rows if x.get("dimension") == d), None)
        values.append(float(r.get("mean_mean_delta", 0.0)) if r else 0.0)

    # 闭合雷达多边形
    labels = dims + [dims[0]]
    data = values + [values[0]]
    angles = [n / float(len(dims)) * 2 * math.pi for n in range(len(dims))]
    angles += [angles[0]]

    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, data, linewidth=2, color="#1f77b4")
    ax.fill(angles, data, color="#1f77b4", alpha=0.25)
    ax.set_thetagrids([a * 180 / math.pi for a in angles[:-1]], dims)
    ax.set_title("Overall Quality Gap: Good vs Bad Code (9 Dimensions)")
    ax.grid(True, linestyle=":", alpha=0.5)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_global_heatmaps(agg_dimension_csv: str, out_path_prefix: str) -> str:
    """绘制维度统计热力图（行=指标，列=维度）。

    指标：mean_mean_delta / mean_median_delta / mean_min_delta / mean_max_delta / mean_consistency
    输出：{out_path_prefix}/global_heatmap.png
    返回：图片路径
    """
    import csv
    import os
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 matplotlib，安装：pip install matplotlib") from e

    from .schemas import Dimension

    rows = []
    with open(agg_dimension_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    dims = [d.value for d in Dimension]
    metrics = [
        "mean_mean_delta",
        "mean_median_delta",
        "mean_min_delta",
        "mean_max_delta",
        "mean_consistency",
    ]

    # 使用原生 list 构建二维数据，避免依赖 numpy
    mat = [[0.0 for _ in range(len(dims))] for _ in range(len(metrics))]
    for j, d in enumerate(dims):
        r = next((x for x in rows if x.get("dimension") == d), None)
        for i, m in enumerate(metrics):
            mat[i][j] = float(r.get(m, 0.0)) if r else 0.0

    plt.figure(figsize=(12, 4.8))
    im = plt.imshow(mat, aspect="auto", cmap="YlOrRd")
    plt.colorbar(im, fraction=0.046, pad=0.04, label="Value")
    plt.yticks(range(len(metrics)), metrics)
    plt.xticks(range(len(dims)), dims, rotation=30, ha="right")
    plt.title("Quality Gap Statistics Across Multiple Tasks")
    out_path = out_path_prefix
    if os.path.isdir(out_path_prefix):
        out_path = os.path.join(out_path_prefix, "global_heatmap.png")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _pick_font_path(font_path: str | None = None) -> str | None:
    if font_path:
        return font_path
    # 常见中文字体路径（按平台尝试）
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:/Windows/Fonts/simhei.ttf",  # Windows SimHei
        "C:/Windows/Fonts/msyh.ttc",    # Microsoft YaHei
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        try:
            if p and __import__("os").path.exists(p):
                return p
        except Exception:
            pass
    return None


def plot_task_wordcloud(task_json_path: str, out_path: str, *, font_path: str | None = None, background_color: str = "white", max_words: int = 200) -> str:
    """基于单任务 aggregated_keywords 绘制词云。"""
    import json
    import os

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 wordcloud 和 matplotlib：pip install wordcloud pillow matplotlib") from e

    with open(task_json_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content.startswith("{") and content.endswith("}"):
            obj = json.loads(content)
        else:
            obj = json.loads(content.splitlines()[0])

    kws = (obj.get("task_level_agg") or {}).get("aggregated_keywords") or []
    freqs = {}
    for k in kws:
        phrase = str(k.get("phrase", "")).strip()
        if not phrase:
            continue
        w = float(k.get("weight", k.get("weight_sum", 0.0)) or 0.0)
        freqs[phrase] = freqs.get(phrase, 0.0) + max(0.0, w)

    if not freqs:
        # 构造一个占位，避免报错
        freqs = {"No Keywords": 1.0}

    fp = _pick_font_path(font_path)
    
    # 构建 WordCloud 参数，如果没有字体则不传 font_path（使用默认字体）
    wc_params = {
        "width": 1200,
        "height": 800,
        "background_color": background_color,
        "prefer_horizontal": 0.9,
        "collocations": False,
    }
    if fp:  # 只有找到字体文件时才设置
        wc_params["font_path"] = fp
    
    wc = WordCloud(**wc_params).generate_from_frequencies(freqs)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_global_wordcloud(agg_keywords_csv: str, out_path: str, *, font_path: str | None = None, background_color: str = "white", top_k: int = 200) -> str:
    """基于全局关键词 CSV 绘制词云（phrase -> weight_sum）。"""
    import csv
    import os

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 wordcloud 和 matplotlib：pip install wordcloud pillow matplotlib") from e

    rows = []
    with open(agg_keywords_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    rows.sort(key=lambda r: float(r.get("weight_sum", 0.0)), reverse=True)
    rows = rows[:top_k]

    freqs = {}
    for r in rows:
        phrase = str(r.get("phrase", "")).strip()
        if not phrase:
            continue
        w = float(r.get("weight_sum", 0.0) or 0.0)
        freqs[phrase] = freqs.get(phrase, 0.0) + max(0.0, w)

    if not freqs:
        freqs = {"No Keywords": 1.0}

    fp = _pick_font_path(font_path)
    
    # 构建 WordCloud 参数，如果没有字体则不传 font_path（使用默认字体）
    wc_params = {
        "width": 1400,
        "height": 900,
        "background_color": background_color,
        "prefer_horizontal": 0.9,
        "collocations": False,
    }
    if fp:  # 只有找到字体文件时才设置
        wc_params["font_path"] = fp
    
    wc = WordCloud(**wc_params).generate_from_frequencies(freqs)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.figure(figsize=(14, 9))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path
