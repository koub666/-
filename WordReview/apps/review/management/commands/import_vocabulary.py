import os
import json
import re
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from apps.review.models import Words, Review, Books, BookList

class Command(BaseCommand):
    help = 'Import vocabulary from english-vocabulary-master folder'
    
    def handle(self, *args, **options):
        # 定义单词库文件夹路径
        # 当前文件位置：apps/review/management/commands/import_vocabulary.py
        # 需要访问的位置：../english-vocabulary-master
        current_dir = os.path.dirname(os.path.abspath(__file__))
        vocab_folder = os.path.abspath(os.path.join(current_dir, '../../../../../english-vocabulary-master'))
        
        # 处理JSON文件
        self.import_json_files(vocab_folder)
        
        # 处理TXT文件
        self.import_txt_files(vocab_folder)
        
        self.stdout.write(self.style.SUCCESS('All vocabulary imported successfully!'))
    
    def import_json_files(self, vocab_folder):
        """导入JSON格式的单词库"""
        json_folder = os.path.join(vocab_folder, 'json')
        if not os.path.exists(json_folder):
            return
        
        # 获取已导入的单词书列表
        existing_books = set(Books.objects.values_list('BOOK', flat=True))
        
        for filename in os.listdir(json_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(json_folder, filename)
                
                # 解析文件名获取单词书信息
                book_match = re.match(r'(\d+)-(.*?)-(\w+)\.json', filename)
                if book_match:
                    book_id = book_match.group(1)
                    book_name = book_match.group(2)
                    book_order = book_match.group(3)
                else:
                    book_name = filename.replace('.json', '')
                    book_id = '0'
                
                # 跳过已导入的单词书
                if book_name in existing_books:
                    self.stdout.write(f'Skipping {filename} (already imported)...')
                    continue
                
                self.stdout.write(f'Importing {filename}...')
                
                # 读取JSON文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    words_data = json.load(f)
                
                # 创建单词书记录
                book, created = Books.objects.get_or_create(
                    BOOK=book_name,
                    defaults={
                        'BOOK_zh': book_name,
                        'BOOK_abbr': book_id,
                        'begin_index': 0,
                        'hide': False
                    }
                )
                
                # 导入单词
                list_num = 1
                unit_num = 1
                for index, word_item in enumerate(words_data):
                    word = word_item['word']
                    
                    # 提取中文释义
                    translations = []
                    for trans_item in word_item['translations']:
                        word_type = trans_item.get('type', '')
                        translations.append(f"{trans_item['translation']} [{word_type}]")
                    mean = '; '.join(translations)
                    
                    # 提取短语（作为记忆法的一部分）
                    phrases = []
                    for phrase_item in word_item.get('phrases', []):
                        phrases.append(f"{phrase_item['phrase']} - {phrase_item['translation']}")
                    note = '\n'.join(phrases)
                    
                    # 导入到Words表
                    words_obj, created = Words.objects.update_or_create(
                        word=word,
                        defaults={
                            'mean': mean,
                            'note': note,
                            'modify_time': now(),
                            'rate': -1,
                            'flag': 0
                        }
                    )
                    
                    # 导入到Review表
                    Review.objects.update_or_create(
                        word=word,
                        BOOK=book_name,
                        defaults={
                            'LIST': list_num,
                            'UNIT': unit_num,
                            'INDEX': index + 1,
                            'total_num': 0,
                            'forget_num': 0,
                            'rate': -1,
                            'history': '',
                            'flag': 0
                        }
                    )
                
                # 创建BookList记录
                BookList.objects.update_or_create(
                    BOOK=book_name,
                    LIST=list_num,
                    defaults={
                        'review_dates': '',
                        'review_dates_plus': '',
                        'list_rate': -1,
                        'recent_list_rate': -1,
                        'word_num': len(words_data),
                        'ebbinghaus_counter': 0,
                        'unlearned_num': len(words_data)
                    }
                )
                
                self.stdout.write(self.style.SUCCESS(f'Imported {len(words_data)} words from {filename}'))
    
    def import_txt_files(self, vocab_folder):
        """导入TXT格式的单词库"""
        # 获取已导入的单词书列表
        existing_books = set(Books.objects.values_list('BOOK', flat=True))
        
        # 遍历vocab_folder中的所有TXT文件
        for filename in os.listdir(vocab_folder):
            if filename.endswith('.txt') and filename != '.gitignore':
                file_path = os.path.join(vocab_folder, filename)
                
                # 解析文件名获取单词书信息
                book_match = re.match(r'(\d+)\s*(.*?)-\s*(\w+)\.txt', filename)
                if book_match:
                    book_id = book_match.group(1)
                    book_name = book_match.group(2)
                    book_order = book_match.group(3)
                else:
                    book_name = filename.replace('.txt', '')
                    book_id = '0'
                
                # 跳过已导入的单词书，以及处理名称映射
                # 映射中文名称到英文名称，避免重复导入
                name_mapping = {
                    '初中': '初中',
                    '高中': '高中',
                    '四级': 'CET4',
                    '六级': 'CET6',
                    '考研': '考研',
                    '托福': '托福',
                    'SAT': 'SAT'
                }
                mapped_name = name_mapping.get(book_name, book_name)
                
                if mapped_name in existing_books:
                    self.stdout.write(f'Skipping {filename} (already imported as {mapped_name})...')
                    continue
                
                # 更新为映射后的名称
                book_name = mapped_name
                
                self.stdout.write(f'Importing {filename}...')
                
                # 创建单词书记录
                book, created = Books.objects.get_or_create(
                    BOOK=book_name,
                    defaults={
                        'BOOK_zh': book_name,
                        'BOOK_abbr': book_id,
                        'begin_index': 0,
                        'hide': False
                    }
                )
                
                # 读取TXT文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 导入单词
                list_num = 1
                unit_num = 1
                word_count = 0
                
                # 批量导入优化
                words_to_create = []
                review_to_create = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析TXT行：单词 n. 释义 v. 其他信息
                    match = re.match(r'(\w+)\s+(.*)', line)
                    if match:
                        word = match.group(1)
                        info = match.group(2)
                        
                        # 提取释义和词性
                        mean_parts = []
                        current_part = []
                        for part in re.finditer(r'(adj\.|adv\.|n\.|v\.|prep\.|conj\.|pron\.|num\.|int\.|vt\.|vi\.)', info):
                            if current_part:
                                mean_parts.append(''.join(current_part).strip())
                            current_part = [part.group(), ' ']
                        if current_part:
                            mean_parts.append(''.join(current_part).strip())
                        mean = '; '.join(mean_parts)
                        
                        # 准备批量导入数据
                        words_to_create.append({
                            'word': word,
                            'mean': mean,
                            'modify_time': now(),
                            'rate': -1,
                            'flag': 0
                        })
                        
                        review_to_create.append({
                            'word': word,
                            'BOOK': book_name,
                            'LIST': list_num,
                            'UNIT': unit_num,
                            'INDEX': word_count + 1,
                            'total_num': 0,
                            'forget_num': 0,
                            'rate': -1,
                            'history': '',
                            'flag': 0
                        })
                        
                        word_count += 1
                
                # 批量导入到Words表
                for word_data in words_to_create:
                    Words.objects.update_or_create(
                        word=word_data['word'],
                        defaults=word_data
                    )
                
                # 批量导入到Review表
                for review_data in review_to_create:
                    Review.objects.update_or_create(
                        word=review_data['word'],
                        BOOK=review_data['BOOK'],
                        defaults=review_data
                    )
                
                # 创建BookList记录
                BookList.objects.update_or_create(
                    BOOK=book_name,
                    LIST=list_num,
                    defaults={
                        'review_dates': '',
                        'review_dates_plus': '',
                        'list_rate': -1,
                        'recent_list_rate': -1,
                        'word_num': word_count,
                        'ebbinghaus_counter': 0,
                        'unlearned_num': word_count
                    }
                )
                
                self.stdout.write(self.style.SUCCESS(f'Imported {word_count} words from {filename}'))
