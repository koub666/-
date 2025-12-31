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
        vocab_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'english-vocabulary-master')
        
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
        
        for filename in os.listdir(json_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(json_folder, filename)
                self.stdout.write(f'Importing {filename}...')
                
                # 解析文件名获取单词书信息
                book_match = re.match(r'(\d+)-(.*?)-(\w+)\.json', filename)
                if book_match:
                    book_id = book_match.group(1)
                    book_name = book_match.group(2)
                    book_order = book_match.group(3)
                else:
                    book_name = filename.replace('.json', '')
                    book_id = '0'
                
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
                        if trans_item['type'] == 'n':
                            translations.append(f"{trans_item['translation']} [{trans_item['type']}]")
                        else:
                            translations.append(f"{trans_item['translation']} [{trans_item['type']}]")
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
        # 遍历vocab_folder中的所有TXT文件
        for filename in os.listdir(vocab_folder):
            if filename.endswith('.txt') and filename != '.gitignore':
                file_path = os.path.join(vocab_folder, filename)
                self.stdout.write(f'Importing {filename}...')
                
                # 解析文件名获取单词书信息
                book_match = re.match(r'(\d+)\s*(.*?)-\s*(\w+)\.txt', filename)
                if book_match:
                    book_id = book_match.group(1)
                    book_name = book_match.group(2)
                    book_order = book_match.group(3)
                else:
                    book_name = filename.replace('.txt', '')
                    book_id = '0'
                
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
                        
                        # 导入到Words表
                        words_obj, created = Words.objects.update_or_create(
                            word=word,
                            defaults={
                                'mean': mean,
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
                                'INDEX': word_count + 1,
                                'total_num': 0,
                                'forget_num': 0,
                                'rate': -1,
                                'history': '',
                                'flag': 0
                            }
                        )
                        
                        word_count += 1
                
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
