#!/usr/bin/env python3
"""
删除无效的单词书记录
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

print('Deleting invalid books...')
print('-' * 50)

# 要删除的无效单词书
invalid_books = ['六级', '四级']

for book_name in invalid_books:
    # 检查是否存在该单词书
    try:
        book = Books.objects.get(BOOK=book_name)
        
        # 获取相关的Review记录数量
        review_count = Review.objects.filter(BOOK=book_name).count()
        # 获取相关的BookList记录数量
        booklist_count = BookList.objects.filter(BOOK=book_name).count()
        
        print(f"Found invalid book: {book_name}")
        print(f"  Reviews: {review_count}")
        print(f"  BookLists: {booklist_count}")
        
        # 删除相关记录
        Review.objects.filter(BOOK=book_name).delete()
        BookList.objects.filter(BOOK=book_name).delete()
        book.delete()
        
        print(f"  Successfully deleted {book_name}")
    except Books.DoesNotExist:
        print(f"Book {book_name} not found")
    
    print('-' * 50)

print('Done!')
