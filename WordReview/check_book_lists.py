#!/usr/bin/env python3
"""
检查数据库中每个单词书的List情况
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
from apps.review.models import Books, BookList, Review

print('Checking book lists...')
print('-' * 50)

# 获取所有单词书
books = Books.objects.all()

for book in books:
    # 获取该单词书的所有List
    book_lists = BookList.objects.filter(BOOK=book.BOOK)
    # 获取该单词书的单词数量
    word_count = Review.objects.filter(BOOK=book.BOOK).count()
    
    print(f"Book: {book.BOOK} ({book.BOOK_zh})")
    print(f"  Lists: {book_lists.count()}")
    print(f"  Word count: {word_count}")
    
    # 打印每个List的信息
    for book_list in book_lists:
        print(f"    List {book_list.LIST}: {book_list.word_num} words")
    
    print('-' * 50)
