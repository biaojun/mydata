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

    dims = [d.value for d in Dimension]
    per_dim_values = {d: [] for d in dims}
    for cmp in obj.get("per_bad_comparisons") or []:
        dim_scores = (cmp.get("dimension_scores") or {})
        for d in dims:
            detail = dim_scores.get(d)
            if not detail:
                continue
            try:
                per_dim_values[d].append(float(detail.get("delta", 0.0)))
            except Exception:
                continue

    def _stats(vals):
        if not vals:
            return 0.0, 0.0, 0.0, 0.0
        xs = sorted(vals)
        n = len(xs)
        mean_val = sum(xs) / n
        if n % 2 == 1:
            median_val = xs[n // 2]
        else:
            median_val = (xs[n // 2 - 1] + xs[n // 2]) / 2.0
        return mean_val, median_val, xs[0], xs[-1]

    means = []
    meds = []
    mins = []
    maxs = []
    for d in dims:
        mean_val, median_val, min_val, max_val = _stats(per_dim_values[d])
        means.append(mean_val)
        meds.append(median_val)
        mins.append(min_val)
        maxs.append(max_val)

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

    默认取 Top-20（按 per_bad discriminative_keywords 累积权重排序）。
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

    kw_totals = {}
    for cmp in obj.get("per_bad_comparisons") or []:
        for kw in cmp.get("discriminative_keywords") or []:
            phrase = str(kw.get("phrase", ""))
            dim = str(kw.get("dimension", ""))
            if hasattr(dim, "value"):
                dim = str(dim.value)
            if not phrase:
                continue
            try:
                weight = float(kw.get("weight", kw.get("weight_sum", 0.0)) or 0.0)
            except Exception:
                continue
            key = (phrase, dim)
            kw_totals[key] = kw_totals.get(key, 0.0) + weight

    items = [
        {"phrase": phrase, "dimension": dim, "weight": weight}
        for (phrase, dim), weight in kw_totals.items()
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
    """绘制九维全局雷达图，比较 good_code 与 bad_code 的平均得分。"""
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
    good_values = []
    bad_values = []
    for d in dims:
        r = next((x for x in rows if x.get("dimension") == d), None)
        good_values.append(float(r.get("avg_good_score", 0.0)) if r else 0.0)
        bad_values.append(float(r.get("avg_bad_score", 0.0)) if r else 0.0)

    # 闭合雷达多边形
    labels = dims + [dims[0]]
    good_data = good_values + [good_values[0]]
    bad_data = bad_values + [bad_values[0]]
    angles = [n / float(len(dims)) * 2 * math.pi for n in range(len(dims))]
    angles += [angles[0]]

    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, good_data, linewidth=2, color="#2ca02c", label="Good code")
    ax.fill(angles, good_data, color="#2ca02c", alpha=0.25)
    ax.plot(angles, bad_data, linewidth=2, color="#d62728", label="Bad code")
    ax.fill(angles, bad_data, color="#d62728", alpha=0.15)
    ax.set_ylim(0, 5)
    ax.set_thetagrids([a * 180 / math.pi for a in angles[:-1]], dims)
    ax.set_title("Average Scores by Dimension: Good vs Bad Code")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_global_heatmaps(agg_dimension_csv: str, out_path_prefix: str) -> str:
    """绘制维度统计热力图：上=delta类指标(发散色, 0居中)，下=一致性(顺序色)。

    指标：avg_of_means / avg_of_medians / avg_of_mins / avg_of_maxes / avg_consistency
    输出：{out_path_prefix}/global_heatmap.png
    返回：图片路径
    """
    import csv
    import os
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        import matplotlib.gridspec as gridspec
    except Exception as e:
        raise ImportError("需要 matplotlib，安装：pip install matplotlib") from e

    from .schemas import Dimension

    rows = []
    with open(agg_dimension_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    dims = [d.value for d in Dimension]
    metrics_all = [
        "avg_of_means",
        "avg_of_medians",
        "avg_of_mins",
        "avg_of_maxes",
        "avg_consistency",
    ]

    metric_labels = {
        "avg_of_means": "Avg of mean deltas",
        "avg_of_medians": "Avg of median deltas",
        "avg_of_mins": "Avg of min deltas",
        "avg_of_maxes": "Avg of max deltas",
        "avg_consistency": "Avg consistency (τ≥2)",
    }

    # 构建二维数据矩阵
    mat = [[0.0 for _ in range(len(dims))] for _ in range(len(metrics_all))]
    for j, d in enumerate(dims):
        r = next((x for x in rows if x.get("dimension") == d), None)
        for i, m in enumerate(metrics_all):
            mat[i][j] = float(r.get(m, 0.0)) if r else 0.0

    # 拆分：delta 指标(前四行) + consistency(最后一行)
    delta_rows_idx = [0, 1, 2, 3]
    cons_row_idx = 4
    delta_mat = [mat[i] for i in delta_rows_idx]
    cons_mat = [mat[cons_row_idx]]

    # 发散色带：以 0 为中心
    if delta_mat:
        flat = [v for row in delta_mat for v in row]
        if flat:
            max_abs = max(1e-6, max(abs(min(flat)), abs(max(flat))))
        else:
            max_abs = 1.0
    else:
        max_abs = 1.0
    delta_norm = mcolors.TwoSlopeNorm(vcenter=0.0, vmin=-max_abs, vmax=max_abs)

    # 一致性 0..1（容错：若全相等则扩展范围）
    cons_vals = cons_mat[0] if cons_mat else []
    cons_min = min(cons_vals) if cons_vals else 0.0
    cons_max = max(cons_vals) if cons_vals else 1.0
    if cons_min == cons_max:
        cons_min, cons_max = 0.0, max(1.0, cons_max)
    cons_cmap = "Greens"

    # 画两块子图
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1], hspace=0.15)

    # 上：delta 指标
    ax1 = fig.add_subplot(gs[0])
    im1 = ax1.imshow(delta_mat, aspect="auto", cmap="RdBu_r", norm=delta_norm)
    ax1.set_yticks(range(len(delta_rows_idx)))
    ax1.set_yticklabels([metric_labels[metrics_all[i]] for i in delta_rows_idx])
    ax1.set_xticks(range(len(dims)))
    ax1.set_xticklabels(dims, rotation=30, ha="right")
    ax1.set_title("Quality Gap (Delta: Good - Bad), centered at 0")
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Delta (Good - Bad)")

    # 下：一致性
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    im2 = ax2.imshow(cons_mat, aspect="auto", cmap=cons_cmap, vmin=cons_min, vmax=cons_max)
    ax2.set_yticks([0])
    ax2.set_yticklabels([metric_labels["avg_consistency"]])
    ax2.set_xticks(range(len(dims)))
    ax2.set_xticklabels(dims, rotation=30, ha="right")
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Consistency")

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
    """基于单任务 per_bad discriminative_keywords 绘制词云。"""
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

    freqs = {}
    for cmp in obj.get("per_bad_comparisons") or []:
        for k in cmp.get("discriminative_keywords") or []:
            phrase = str(k.get("phrase", "")).strip()
            if not phrase:
                continue
            try:
                w = float(k.get("weight", k.get("weight_sum", 0.0)) or 0.0)
            except Exception:
                continue
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


def plot_pattern_wordcloud(pattern_csv: str, out_path: str, *, font_path: str | None = None, background_color: str = "white", top_k: int = 200) -> str:
    """基于正/反向模式 CSV 绘制词云（pattern -> count）。"""
    import csv
    import os

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("需要 wordcloud 和 matplotlib：pip install wordcloud pillow matplotlib") from e

    rows = []
    with open(pattern_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    rows.sort(key=lambda r: float(r.get("count", 0.0)), reverse=True)
    rows = rows[:top_k]

    freqs = {}
    for r in rows:
        phrase = str(r.get("pattern", "")).strip()
        if not phrase:
            continue
        count = float(r.get("count", 0.0) or 0.0)
        freqs[phrase] = freqs.get(phrase, 0.0) + max(0.0, count)

    if not freqs:
        freqs = {"No Patterns": 1.0}

    fp = _pick_font_path(font_path)
    wc_params = {
        "width": 1400,
        "height": 900,
        "background_color": background_color,
        "prefer_horizontal": 0.9,
        "collocations": False,
    }
    if fp:
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
