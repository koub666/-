#!/usr/bin/env python3
"""
检查数据库中的单词书情况
"""
import os
import sys

# 添加项目根目录到Python路径
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

# 设置DJANGO_SETTINGS_MODULE环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WordReview.settings')

# 初始化Django
import django
django.setup()

# 导入模型
from apps.review.models import Books

print('Books in database:')
for book in Books.objects.all():
    print(f'- {book.BOOK}: {book.BOOK_zh}')

print('\nBooks count:', Books.objects.count())
