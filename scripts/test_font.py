#!/usr/bin/env python3
"""
Quick script to verify a Chinese font works for matplotlib and wordcloud.

Usage:
  python scripts/test_font.py /path/to/your/font.ttf
  # or rely on env var
  FONT_PATH=/path/to/your/font.ttc python scripts/test_font.py

Outputs:
  - <outdir>/matplotlib_font_test.png
  - <outdir>/wordcloud_font_test.png (if wordcloud is installed)

Notes:
  - On macOS, common fonts include:
      /System/Library/Fonts/PingFang.ttc
      /System/Library/Fonts/STHeiti Light.ttc
      /Library/Fonts/Arial Unicode.ttf
  - If you only want to test matplotlib, add --skip-wordcloud
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional


def _print(msg: str):
    print(f"[font-test] {msg}")


def test_matplotlib(font_path: str, out_png: str, *, text: str, dpi: int = 150) -> bool:
    try:
        import matplotlib
        matplotlib.rcParams['axes.unicode_minus'] = False
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties
    except Exception as e:
        _print(f"matplotlib not available: {e}")
        return False

    try:
        fp = FontProperties(fname=font_path)
        # Create a simple figure with Chinese text
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.set_title("中文字体测试 (matplotlib)", fontproperties=fp)
        ax.text(0.05, 0.6, text, fontproperties=fp, fontsize=16)
        ax.text(0.05, 0.35, "0123456789 AaBbCc Δ−×÷", fontproperties=fp, fontsize=12)
        ax.axis('off')
        os.makedirs(os.path.dirname(out_png) or '.', exist_ok=True)
        fig.tight_layout()
        fig.savefig(out_png, dpi=dpi)
        plt.close(fig)
        _print(f"matplotlib OK -> {out_png}")
        return True
    except Exception as e:
        _print(f"matplotlib render failed: {e}")
        return False


def test_wordcloud(font_path: str, out_png: str, *, dpi: int = 150) -> bool:
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
    except Exception as e:
        _print(f"wordcloud not available: {e} (pip install wordcloud pillow)")
        return False

    try:
        # A tiny Chinese dictionary for frequencies
        freqs = {
            "你好": 10,
            "世界": 8,
            "代码质量": 7,
            "鲁棒性": 6,
            "可读性": 5,
            "可维护性": 5,
            "性能": 4,
            "测试": 4,
            "安全依赖": 3,
            "风格一致性": 3,
        }
        wc = WordCloud(
            width=800,
            height=500,
            background_color='white',
            prefer_horizontal=0.9,
            collocations=False,
            font_path=font_path,
        ).generate_from_frequencies(freqs)

        os.makedirs(os.path.dirname(out_png) or '.', exist_ok=True)
        plt.figure(figsize=(8, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(out_png, dpi=dpi)
        plt.close()
        _print(f"wordcloud OK -> {out_png}")
        return True
    except Exception as e:
        _print(f"wordcloud render failed: {e}")
        return False


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Test a Chinese font with matplotlib and wordcloud")
    parser.add_argument("font", nargs="?", default=os.environ.get("FONT_PATH"), help="Path to font file (.ttf/.ttc)")
    parser.add_argument("--outdir", default="font_test_outputs", help="Output directory for test images")
    parser.add_argument("--text", default="中文字体测试：你好，世界！代码质量/鲁棒性/可读性/性能/安全依赖/风格一致性", help="Chinese text for matplotlib test")
    parser.add_argument("--skip-wordcloud", action="store_true", help="Skip wordcloud test")
    parser.add_argument("--dpi", type=int, default=150, help="Image DPI")
    args = parser.parse_args(argv)

    if not args.font:
        _print("Please provide a font path as an argument or set FONT_PATH env var.")
        parser.print_help()
        return 2

    font_path = os.path.expanduser(args.font)
    if not os.path.exists(font_path):
        _print(f"Font not found: {font_path}")
        return 2

    os.makedirs(args.outdir, exist_ok=True)

    ok_mpl = test_matplotlib(font_path, os.path.join(args.outdir, "matplotlib_font_test.png"), text=args.text, dpi=args.dpi)

    ok_wc = True
    if not args.skip_wordcloud:
        ok_wc = test_wordcloud(font_path, os.path.join(args.outdir, "wordcloud_font_test.png"), dpi=args.dpi)

    if ok_mpl and ok_wc:
        _print("All tests passed.")
        return 0
    elif ok_mpl:
        _print("Matplotlib test passed; wordcloud failed or skipped.")
        return 0 if args.skip_wordcloud else 1
    else:
        _print("Matplotlib test failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
