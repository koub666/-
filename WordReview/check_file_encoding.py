#!/usr/bin/env python3
"""
检查文件编码
"""
import chardet
import os

# 文件路径
file_path = "..\english-vocabulary-master\4 六级-乱序.txt"

# 读取文件内容
with open(file_path, 'rb') as f:
    content = f.read()

# 检测编码
result = chardet.detect(content)
print(f"File: {file_path}")
print(f"Encoding: {result['encoding']}")
print(f"Confidence: {result['confidence']}")
print(f"Language: {result['language']}")

# 尝试用检测到的编码读取文件
print("\nFile content (first 5 lines):")
try:
    with open(file_path, 'r', encoding=result['encoding']) as f:
        for i, line in enumerate(f):
            if i < 5:
                print(line.strip())
            else:
                break
except UnicodeDecodeError as e:
    print(f"Failed to read with {result['encoding']}: {e}")
    # 尝试用其他编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                print(f"\nTrying {enc}:")
                for i, line in enumerate(f):
                    if i < 5:
                        print(line.strip())
                    else:
                        break
                break
        except UnicodeDecodeError:
            continue
