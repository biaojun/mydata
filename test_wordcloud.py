#!/usr/bin/env python3
"""测试词云生成功能"""

import sys

def test_wordcloud():
    """测试词云库是否正常工作"""
    print("=" * 60)
    print("🧪 测试词云功能")
    print("=" * 60)
    
    # 1. 检查 wordcloud 库
    print("\n1️⃣ 检查 wordcloud 库...")
    try:
        from wordcloud import WordCloud
        print("   ✓ wordcloud 已安装")
    except ImportError:
        print("   ❌ wordcloud 未安装")
        print("   安装命令: pip install wordcloud pillow")
        return False
    
    # 2. 检查 matplotlib
    print("\n2️⃣ 检查 matplotlib...")
    try:
        import matplotlib.pyplot as plt
        print("   ✓ matplotlib 已安装")
    except ImportError:
        print("   ❌ matplotlib 未安装")
        print("   安装命令: pip install matplotlib")
        return False
    
    # 3. 测试生成简单词云（不使用中文字体）
    print("\n3️⃣ 测试生成英文词云（无需字体）...")
    try:
        test_words = {
            "error_handling": 10.0,
            "type_annotation": 8.5,
            "input_validation": 7.3,
            "modular_design": 6.8,
            "unit_testing": 5.2
        }
        
        wc = WordCloud(
            width=800,
            height=600,
            background_color="white"
        ).generate_from_frequencies(test_words)
        
        print("   ✓ 英文词云生成成功（默认字体）")
        
        # 保存测试
        import os
        test_output = "/tmp/test_wordcloud_en.png"
        plt.figure(figsize=(10, 7))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.savefig(test_output, dpi=150)
        plt.close()
        print(f"   ✓ 已保存到: {test_output}")
        
    except Exception as e:
        print(f"   ❌ 生成失败: {e}")
        return False
    
    # 4. 检查中文字体
    print("\n4️⃣ 检查中文字体支持...")
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:/Windows/Fonts/simhei.ttf",  # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
    ]
    
    found_font = None
    for font in candidates:
        if os.path.exists(font):
            print(f"   ✓ 找到中文字体: {font}")
            found_font = font
            break
    
    if not found_font:
        print("   ⚠️  未找到中文字体（只能生成英文词云）")
        print("   提示: 如需中文支持，设置环境变量:")
        print("   export FONT_PATH=/path/to/your/font.ttf")
    else:
        # 5. 测试中文词云
        print("\n5️⃣ 测试中文词云...")
        try:
            test_words_cn = {
                "异常处理": 10.0,
                "类型注解": 8.5,
                "输入校验": 7.3,
            }
            
            wc = WordCloud(
                width=800,
                height=600,
                background_color="white",
                font_path=found_font
            ).generate_from_frequencies(test_words_cn)
            
            test_output_cn = "/tmp/test_wordcloud_cn.png"
            plt.figure(figsize=(10, 7))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            plt.savefig(test_output_cn, dpi=150)
            plt.close()
            print(f"   ✓ 中文词云生成成功")
            print(f"   ✓ 已保存到: {test_output_cn}")
        except Exception as e:
            print(f"   ❌ 中文词云生成失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 词云功能测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_wordcloud()
    sys.exit(0 if success else 1)
