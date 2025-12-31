from django.contrib import admin
from .models import Words, Books, BookList, Review

# 注册模型到管理界面
admin.site.register(Words)
admin.site.register(Books)
admin.site.register(BookList)
admin.site.register(Review)
