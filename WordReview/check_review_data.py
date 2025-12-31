#!/usr/bin/env python3
"""
检查Review表中的数据，特别是LIST字段的值
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
from apps.review.models import Review, Books

print('Checking Review data...')
print('-' * 50)

# 获取所有单词书
books = Books.objects.all()

for book in books:
    print(f'Book: {book.BOOK}')
    
    # 获取该单词书的Review数据
    reviews = Review.objects.filter(BOOK=book.BOOK).order_by('LIST', 'UNIT', 'INDEX')
    
    # 统计LIST分布
    list_counts = {}
    for review in reviews[:20]:  # 只检查前20条记录
        if review.LIST not in list_counts:
            list_counts[review.LIST] = 0
        list_counts[review.LIST] += 1
    
    print(f'LIST distribution: {list_counts}')
    
    # 打印前5条记录的详细信息
    print('First 5 reviews:')
    for review in reviews[:5]:
        print(f'- {review.word} (LIST: {review.LIST}, UNIT: {review.UNIT}, INDEX: {review.INDEX}, flag: {review.flag})')
    
    # 检查flag<2的记录数量
    active_reviews = reviews.filter(flag__lt=2)
    print(f'Total reviews: {reviews.count()}')
    print(f'Active reviews (flag<2): {active_reviews.count()}')
    
    print('-' * 50)

print('Done!')
