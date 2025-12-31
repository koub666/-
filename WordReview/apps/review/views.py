# -*- coding: utf-8 -*-
"""
单词复习系统视图文件
包含所有页面渲染和API接口实现
"""

# Django核心模块
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

# 自定义模型
from apps.review.models import Review, BookList, Words, Books

# 工具函数
from apps.src.util import ormToJson, valueList
import config
from apps.review.src.init_db import init_db, update_db
from apps.review.src.spider import crawl_other_dict

# 日期时间处理
from datetime import datetime, timedelta, date

# 异常处理
import traceback

# 全局配置
Delay_Hours = 4  # 熬夜学习的时间偏移量
EBBINGHAUS_DAYS = [0, 1, 2, 4, 7, 15, 30]  # 艾宾浩斯遗忘曲线复习间隔天数


# 页面视图

def index(request):
    """
    首页视图
    返回主复习页面
    """
    return render(request, "review.pug")



def temp(request):
    """
    临时测试视图
    用于数据库测试和调试
    """
    # 示例代码：查找包含'abandon'的单词
    # out = Words.objects.filter(word__icontains='abandon')
    # for w in out:
    #     print(w.word, ".")
    #     print(w.word.count(' '))
    #     print(w.id)
    # print(out)
    
    # 更新单词数据库
    update_db(Words)
    return render(request, "homepage.pug")



def import_db(request):
    """
    数据库导入页面视图
    处理单词数据导入功能
    """
    if request.method == 'POST':
        # 获取表单数据
        post = request.POST
        print(f"导入表单数据: {post}")
        
        # 解析表单字段
        BOOK = post.get('BOOK')          # 单词书英文名称
        BOOK_zh = post.get('BOOK_zh')    # 单词书中文名称
        BOOK_abbr = post.get('BOOK_abbr')  # 单词书缩写
        excel_path = post.get('excel_path')  # Excel文件路径

        # 验证begin_index参数
        try:
            begin_index = int(post.get('begin_index'))  # 列表起始索引（0或1）
            if begin_index not in [0, 1]:
                return render(request, "import_db.pug",
                              {'message': '请输入 0 或 1！'})
        except ValueError:
            return render(request, "import_db.pug", {'message': '请输入 0 或 1！'})
        
        print(f"导入参数: {BOOK}, {BOOK_zh}, {BOOK_abbr}, {begin_index}, {excel_path}")

        # 执行数据库导入
        try:
            init_db(BOOK, BOOK_zh, BOOK_abbr, begin_index, excel_path, Books,
                    Review, BookList, Words)
        except Exception as e:
            # 记录导入错误
            print(f"导入错误: {traceback.format_exc()}")
            return render(request, "import_db.pug", {'message': str(e)})
        
        # 导入成功，重定向到主页面
        return redirect('/review')
    
    # GET请求，返回导入页面
    return render(request, "import_db.pug")


# API接口

@csrf_exempt
def review_lists(request):
    """
    API接口：复习完成后更新单词列表状态
    处理复习列表的完成状态更新，包括艾宾浩斯复习进度
    
    请求参数：
        list: 复习列表范围，如"1"或"1-3"
        book: 单词书名称
        yesterday_mode: 是否为昨日重现模式
    
    返回：
        JSON响应，包含操作状态和消息
    """
    post = request.POST
    
    # 计算今天的日期，考虑熬夜情况（减去Delay_Hours小时）
    today = datetime.now() - timedelta(hours=Delay_Hours)
    today_str = today.strftime('%Y-%m-%d')
    
    # 昨日重现模式处理
    if post.get('yesterday_mode') == 'true':
        LIST = 0
        while True:
            print(f"处理昨日重现列表: {LIST}")
            try:
                # 获取或创建昨日重现的BookList记录
                book_list = BookList.objects.get(BOOK='WORD_REVIEW', LIST=LIST)
            except BookList.DoesNotExist:
                # 如果BOOK不存在，初始化
                if LIST == 0:
                    from apps.review.src.init_db import init_db_books
                    init_db_books(Books,
                                  'WORD_REVIEW',
                                  '昨日重现自主复习',
                                  '😇',
                                  0,
                                  hide=True)
                # 创建新的BookList记录
                book_list = BookList.objects.create(BOOK='WORD_REVIEW', LIST=LIST)
            
            # 获取现有复习日期
            dates = book_list.review_dates_plus
            # 如果今天还没有复习记录，添加今天的日期
            if today_str != dates.split(';')[-1]:
                book_list.review_dates_plus = (dates + ';' + today_str).strip(';')
                book_list.save()
                print(f"更新复习日期: {book_list.review_dates_plus}")
                break
            else:
                LIST += 1
        LISTS = []  # 昨日重现模式不需要处理具体列表
    else:
        # 正常复习模式，解析列表范围
        list_range = post.get('list').split('-')
        LISTS = [int(i) for i in list_range]
        # 如果是范围，转换为列表
        if len(LISTS) == 2:
            LISTS = list(range(LISTS[0], LISTS[1] + 1))
        BOOK = post.get('book')

    msg = 'done'
    status = 200
    
    # 处理每个列表
    for LIST in LISTS:
        try:
            # 获取未掌握的单词（flag < 1）
            ld = Review.objects.filter(BOOK=BOOK, LIST=LIST, flag__lt=1)
            # 获取已掌握的单词（flag > 0）
            ld_pass = Review.objects.filter(BOOK=BOOK, LIST=LIST, flag__gt=0)
            # 获取对应的BookList记录
            L_db = BookList.objects.get(BOOK=BOOK, LIST=LIST)
        except Exception as e:
            msg = f'获取数据异常：{str(e)}'
            status = 501
            break

        # 更新列表单词总数
        L_db.word_num = len(ld) + len(ld_pass)

        # 计算背过的单词进度
        reviewed_words = Review.objects.filter(LIST=LIST, BOOK=BOOK).exclude(rate=-1).count()
        list_rate = reviewed_words / L_db.word_num if L_db.word_num > 0 else 0

        # 如果还没有背过这个列表
        if list_rate == 0 and len(ld) > 0:
            status = 404
            msg = '你好像还没背过这个 List 诶 😳'
            continue

        # 更新未掌握单词数量
        L_db.unlearned_num = len(ld)
        # 更新单词复习次数集合
        L_db.review_word_counts = ';'.join(
            set([str(t[0]) for t in ld.values_list('total_num')]))

        # 更新列表记忆率
        L_db.list_rate = list_rate
        
        # 计算近期记忆率
        recent_history = ''
        for word in ld:
            recent_history += word.history[-2:]  # 取每个单词最近2次复习记录
        # 计算近期记忆成功率
        L_db.recent_list_rate = recent_history.count('1') / len(recent_history) if recent_history else 0

        # 艾宾浩斯时间处理
        if 0 < L_db.ebbinghaus_counter < len(EBBINGHAUS_DAYS):
            # 当前处于艾宾浩斯复习周期中
            ebbinghaus_counter = L_db.ebbinghaus_counter
            # 计算理论上下一次复习日期
            should_next_date = datetime.strptime(
                L_db.review_dates.split(';')[-1], '%Y-%m-%d') + timedelta(
                    days=EBBINGHAUS_DAYS[ebbinghaus_counter])
            
            # 如果今天已经到了或超过理论复习日期
            if (today - should_next_date).days >= 0:
                print(f"理论复习日期: {should_next_date}")
                # 更新艾宾浩斯计数器和复习日期
                L_db.ebbinghaus_counter += 1
                L_db.review_dates += ';' + today_str
                L_db.last_review_date = today_str
            elif today_str != L_db.review_dates_plus.split(';')[-1]:
                # 自愿复习，更新自愿复习日期
                if L_db.review_dates_plus:
                    L_db.review_dates_plus += ';' + today_str
                else:
                    L_db.review_dates_plus = today_str
        elif L_db.ebbinghaus_counter == 0:
            # 首次复习
            L_db.last_review_date = today_str
            L_db.ebbinghaus_counter = 1
            L_db.review_dates = today_str
            # 同时更新自愿复习日期
            if not L_db.review_dates_plus or today_str not in L_db.review_dates_plus.split(';'):
                if L_db.review_dates_plus:
                    L_db.review_dates_plus += ';' + today_str
                else:
                    L_db.review_dates_plus = today_str
        else:
            # 已完成艾宾浩斯一周目
            L_db.ebbinghaus_counter = 0
            print(f'列表 {LIST} 已完成艾宾浩斯复习周期')

        # 保存更新
        try:
            L_db.save()
        except Exception as e:
            msg = f'保存数据异常：{str(e)}'
            status = 502
            break
    
    # 返回响应
    data = {'msg': msg, 'status': status}
    return JsonResponse(data)


@csrf_exempt
def update_note(request):
    """
    API接口：更新单词笔记
    用于更新单词的自定义笔记
    
    请求参数：
        word: 单词
        note: 笔记内容
    
    返回：
        JSON响应，包含操作状态和消息
    """
    post = request.POST
    msg = 'done'
    status = 200
    
    try:
        print(f"更新笔记数据: {post}")
        # 获取单词对象
        word = Words.objects.get(word=post.get('word'))
        # 更新笔记
        word.note = post.get('note')
        word.save()
    except Exception as e:
        msg = str(e)
        status = 501
    
    return JsonResponse({'msg': msg, 'status': status})


@csrf_exempt
def update_word_flag(request):
    """
    API接口：更新单词标记
    更新单词的标记状态（太简单、重难词等）
    
    请求参数：
        word: 单词
        list: 列表号
        book: 单词书
        flag: 新标记值
        last_flag: 旧标记值
        yesterday_mode: 是否为昨日重现模式
    
    返回：
        JSON响应，包含操作状态和消息
    """
    post = request.POST
    msg = 'done'
    status = 200
    
    try:
        # 昨日重现模式处理
        if post.get('yesterday_mode') == 'true':
            words = [Words.objects.get(word=post.get('word'))]
        else:
            # 正常模式，获取单词和对应的复习记录
            words = [Words.objects.get(word=post.get('word'))]
            
            # 如果是从正向标签退回默认，需要更新所有列表中的该单词
            if post.get('flag') == '0' and int(post.get('last_flag')) > 0:
                words += [
                    rw for rw in Review.objects.filter(word=post.get('word'))
                ]
            else:
                # 否则只更新当前列表中的该单词
                words.append(
                    Review.objects.get(word=post.get('word'),
                                       LIST=post.get('list'),
                                       BOOK=post.get('book')))
        
        # 更新所有相关单词的标记
        for word in words:
            word.flag = post.get('flag')
            word.save()
    except Exception as e:
        msg = str(e)
        status = 501
    
    return JsonResponse({'msg': msg, 'status': status})


@csrf_exempt
def spider_other_dict(request):
    """
    API接口：爬取外部词典数据
    从外部词典网站（如dict.cn）获取单词翻译和例句
    
    请求参数：
        word: 要查询的单词
        url: 词典网站URL
    
    返回：
        JSON响应，包含爬取状态和数据
    """
    # 调用爬虫函数获取数据
    status, data = crawl_other_dict(request.POST.get('word'),
                                    request.POST.get('url'))
    return JsonResponse({'status': status, 'data': data})


@csrf_exempt
def review_a_word(request):
    """
    API接口：更新单词复习记录
    在数据库中更新用户对单词的记忆情况
    
    请求参数：
        word: 单词
        remember: 是否记住（true/false）
        list: 列表号
        book: 单词书
        note: 笔记内容
        last_forget_num: 上次忘记次数
        repeat: 是否为重复复习
        yesterday_mode: 是否为昨日重现模式
    
    返回：
        JSON响应，包含操作状态和消息
    """
    post = request.POST
    
    try:
        # 获取单词基本信息
        word = Words.objects.get(word=post.get('word'))
        
        # 根据复习模式确定要更新的数据库表
        if post.get('repeat') == 'true' or post.get('yesterday_mode') == 'true':
            # 重复复习或昨日重现模式，只更新Words表
            word_dbs = [word]
        else:
            # 正常复习模式，获取或创建Review记录
            word_in_list, created = Review.objects.get_or_create(
                word=post.get('word'),
                BOOK=post.get('book'),
                LIST=post.get('list'),
                defaults={
                    'total_num': 0,
                    'forget_num': 0,
                    'rate': 0,
                    'UNIT': 1,
                    'INDEX': 1,
                    'history': ''
                }
            )
            word_dbs = [word, word_in_list]
    except Exception as e:
        # 数据库操作异常
        return JsonResponse({'msg': '数据库损坏！' + str(e), 'status': 500})

    # 更新数据库
    # 更新笔记（如果有）
    if post.get('note') != 'false':
        word.note = post.get('note')
    # 更新上次忘记次数
    word.last_forget_num = post.get('last_forget_num')

    # 更新复习记录
    for w in word_dbs:
        w.total_num += 1  # 总复习次数+1
        
        if post.get('remember') == 'true':
            # 记住了，历史记录添加'1'
            w.history += '1'
        elif post.get('remember') == 'false':
            # 没记住，历史记录添加'0'，忘记次数+1
            w.history += '0'
            w.forget_num += 1
        
        # 更新遗忘率
        w.rate = word.forget_num / word.total_num
        w.save()
    
    # 实时更新BookList模型，确保首页进度一致
    if post.get('yesterday_mode') != 'true':
        try:
            list_id = int(post.get('list'))
            book = post.get('book')
            
            # 获取当前列表的所有复习数据
            list_reviews = Review.objects.filter(LIST=list_id, BOOK=book)
            list_data = list_reviews.filter(flag__lt=2)
            list_data_pass = list_reviews.filter(flag__gt=0)
            
            # 计算当前进度
            total_words = list_reviews.count()
            unlearned_words = len(list_data)
            
            # 计算list_rate: 已复习单词的百分比
            reviewed_words = list_reviews.exclude(rate=-1).count()
            list_rate = reviewed_words / total_words if total_words > 0 else 0
            
            # 计算recent_list_rate: 近期复习成功率
            recent_history = ''.join([w.history[-2:] for w in list_data if w.history])
            recent_rate = recent_history.count('1') / len(recent_history) if recent_history else 0
            
            # 获取或创建BookList记录
            book_list, created = BookList.objects.get_or_create(
                BOOK=book,
                LIST=list_id,
                defaults={
                    'word_num': total_words,
                    'unlearned_num': unlearned_words,
                    'list_rate': list_rate,
                    'recent_list_rate': recent_rate,
                    'ebbinghaus_counter': 0,
                    'review_dates': '',
                    'review_dates_plus': ''
                }
            )
            
            # 获取今天的日期字符串
            today = datetime.now() - timedelta(hours=Delay_Hours)
            today_str = today.strftime('%Y-%m-%d')
            
            # 更新现有BookList记录
            if not created:
                book_list.word_num = total_words
                book_list.unlearned_num = unlearned_words
                book_list.list_rate = list_rate
                book_list.recent_list_rate = recent_rate
                
                # 实时更新复习日期
                # 检查今天的日期是否已经在review_dates_plus中
                review_dates_plus = book_list.review_dates_plus.split(';') if book_list.review_dates_plus else []
                if today_str not in review_dates_plus:
                    if book_list.review_dates_plus:
                        book_list.review_dates_plus += ';' + today_str
                    else:
                        book_list.review_dates_plus = today_str
                
                # 如果是首次复习（ebbinghaus_counter == 0），也更新review_dates
                if book_list.ebbinghaus_counter == 0:
                    if not book_list.review_dates:
                        book_list.review_dates = today_str
                    elif today_str not in book_list.review_dates.split(';'):
                        book_list.review_dates += ';' + today_str
                
                book_list.save()
                
        except Exception as e:
            print(f"更新BookList时出错: {e}")
    
    # 返回成功响应
    data = {'msg': 'done', 'status': 200}
    return JsonResponse(data)



def get_word(request):
    """
    API接口：获取复习单词列表
    根据请求参数返回要复习的单词列表
    
    请求参数：
        book: 单词书
        list: 列表号或范围
        limit: 限制返回数量
    
    返回：
        JSON响应，包含单词列表和相关配置
    """
    # 字段映射：将数据库字段名转换为前端使用的字段名
    pankeys = {
        'total_num': 'panTotalNum',    # 总复习次数
        'forget_num': 'panForgetNum',  # 忘记次数
        'rate': 'panRate',             # 遗忘率
        'history': 'panHistory',       # 复习历史
        'flag': 'panFlag',             # 标记
    }
    
    sortType = ['乱序', '记忆序']  # 默认排序方式
    msg = ''  # 返回消息
    mode = 'normal'  # 复习模式

    # 获取并解码URL参数
    BOOK = request.GET.get('book')
    LIST = request.GET.get('list')
    limit = request.GET.get('limit')
    
    # Django已经自动解码了URL参数，无需再次解码
    
    # 检查BOOK是否在数据库中，如果不在，尝试进行名称映射
    all_books = [b.BOOK for b in Books.objects.all()]
    if BOOK and BOOK not in all_books:
        # 获取所有单词书的中文名称映射
        book_mapping = {b.BOOK_zh: b.BOOK for b in Books.objects.all()}
        # 尝试根据中文名称进行映射
        if BOOK in book_mapping:
            BOOK = book_mapping[BOOK]

    # 判断是否为昨日重现模式
    yesterday_mode = BOOK == '' and LIST == ''
    Delay_Hours = 0  # 昨日重现模式下使用0小时偏移

    if yesterday_mode:
        # 昨日重现模式：复习最近4天内忘记的单词
        mode = 'yesterday'
        # 计算日期范围
        day0 = datetime.now() - timedelta(days=4, hours=Delay_Hours)
        today = datetime.now() - timedelta(hours=Delay_Hours)
        date_range = [
            datetime.strptime(f"{day0.year}-{day0.month}-{day0.day} {Delay_Hours}", '%Y-%m-%d %H'),
            datetime.strptime(f"{today.year}-{today.month}-{today.day} {Delay_Hours}", '%Y-%m-%d %H')
        ]
        
        # 查询需要复习的单词
        list_info = Words.objects.filter(
            modify_time__range=date_range,  # 修改时间在范围内
            last_forget_num__gt=0  # 忘记次数大于0
        ).order_by("rate").order_by("-last_forget_num")  # 按遗忘率和忘记次数排序
        
        msg = f"There are {len(list_info)} words that you need to review😋"
        
        # 处理limit参数，限制返回数量
        try:
            limit_value = int(limit) if limit else 50
            list_info = list_info[:limit_value]
        except ValueError:
            # 如果limit参数不是有效的整数，使用默认值50
            list_info = list_info[:50]
    else:
        # 正常复习模式
        # 解析LIST参数
        LIST_li = [int(i) for i in LIST.split('-')]
        
        if len(LIST_li) == 1:
            # 单个列表
            list_info = Review.objects.filter(LIST=LIST_li[0], BOOK=BOOK, flag__lt=2)
            
            # 安全获取BookList对象，避免抛出异常
            try:
                book_list = BookList.objects.get(LIST=LIST_li[0], BOOK=BOOK)
                # 如果是首次复习，使用顺序排序
                if book_list.ebbinghaus_counter == 0:
                    sortType = ['顺序']
            except BookList.DoesNotExist:
                # 如果BookList不存在，使用默认排序
                pass
        elif len(LIST_li) == 2:
            # 列表范围
            list_info = Review.objects.filter(LIST__range=LIST_li, BOOK=BOOK)
        else:
            # LIST参数格式异常
            raise KeyError('LIST_li 长度异常')

    # 检查list_info是否为空
    if not list_info:
        print(f"调试: list_info为空，参数: BOOK={BOOK}, LIST={LIST}, flag__lt=2")
        
        # 只在非昨日重现模式时执行调试代码
        if not yesterday_mode and 'LIST_li' in locals():
            # 尝试获取所有flag状态的单词
            all_reviews = Review.objects.filter(BOOK=BOOK, LIST=LIST_li[0])
            print(f"调试: 所有复习记录数量: {all_reviews.count()}")
            
            # 打印flag分布
            from django.db.models import Count
            flag_counts = all_reviews.values('flag').annotate(count=Count('flag'))
            print(f"调试: Flag分布: {list(flag_counts)}")
    
    # 将ORM对象转换为JSON格式
    list_info = ormToJson(list_info)
    
    # 为每个单词添加详细信息
    for i, item in enumerate(list_info):
        l = item['fields']
        try:
            if yesterday_mode:
                # 昨日重现模式下，item已经是完整的单词信息
                w = l
            else:
                # 正常模式下，获取详细的单词信息
                word_obj = Words.objects.get(word=l['word'])
                w = ormToJson([word_obj])[0]['fields']
        except Words.DoesNotExist:
            # 单词不存在，返回404错误
            return JsonResponse({
                "msg": f"Word not found:{l['word']}",
                'status': 404
            })

        # 更新字段名称，将数据库字段映射为前端使用的字段
        for old, pan in pankeys.items():
            if old in w:
                w[pan] = w.pop(old)
        
        # 更新原始数据，合并详细信息
        list_info[i]['fields'].update(w)

    # 获取最近复习的单词
    yesterday = datetime.now() - timedelta(days=1, hours=Delay_Hours)
    recent_words = Words.objects.filter(modify_time__gt=date(
        yesterday.year, yesterday.month, yesterday.day)).values_list('word')

    # 获取begin_index，添加异常处理
    try:
        # 根据单词书的begin_index确定显示起始索引
        begin_index = int(Books.objects.get(BOOK=BOOK).begin_index == 0) if BOOK != '' else 0
    except Books.DoesNotExist:
        begin_index = 0
    
    # 构建响应数据
    data = dict(
        data=list_info,  # 单词列表
        status=200,       # 状态码
        sort=sortType,    # 排序方式
        begin_index=begin_index,  # 起始索引
        recent_words=[rw[0] for rw in recent_words],  # 最近复习的单词
        mode=mode,        # 复习模式
        msg=msg           # 返回消息
    )
    return JsonResponse(data)



def get_calendar_data(request):
    """
    API接口：获取日历渲染数据
    返回用于渲染艾宾浩斯复习日历的数据
    
    返回：
        JSON响应，包含日历数据和艾宾浩斯复习间隔
    """
    # 获取所有单词书信息
    books = Books.objects.all()
    book_info = {}
    
    # 构建单词书信息字典
    for b in books:
        book_info[b.BOOK] = {
            'abbr': b.BOOK_abbr,  # 单词书缩写
            'begin_index': 1 if b.begin_index == 0 else 0,  # 起始索引
        }
    
    # 查询需要在日历上显示的BookList记录
    # 条件：艾宾浩斯计数器大于0 或 有自愿复习日期
    db = BookList.objects.filter(
        Q(ebbinghaus_counter__gt=0) | ~Q(review_dates_plus=''))
    
    # 转换为JSON格式
    data = ormToJson(db)
    
    # 为每条记录添加单词书信息
    for d in data:
        d_fields = d['fields']
        d_fields['abbr'] = book_info[d_fields['BOOK']]['abbr']
        d_fields['begin_index'] = book_info[d_fields['BOOK']]['begin_index']

    # 构建响应数据
    response_data = {
        'data': data,  # 日历数据
        'EBBINGHAUS_DAYS': EBBINGHAUS_DAYS,  # 艾宾浩斯复习间隔
        'status': 200  # 状态码
    }
    return JsonResponse(response_data)


# 页面渲染视图

def review(request):
    """
    单词复习页视图
    渲染单词复习页面，传递URL参数给模板
    
    URL参数：
        list: 列表号
        book: 单词书
    """
    # 获取URL参数
    LIST = request.GET.get('list')
    BOOK = request.GET.get('book')
    
    # 返回复习页面，传递参数给模板
    return render(request, "review.pug", locals())



def calendar(request):
    """
    艾宾浩斯日历图页面视图
    渲染日历页面
    """
    return render(request, "calendar.pug")



def homepage(request):
    """
    复习主页视图
    渲染复习主页，展示单词书和列表的复习进度
    """
    # 获取所有未隐藏的单词书，按创建时间倒序排列
    books = Books.objects.filter(hide=False)[::-1]
    
    # 构建单词书信息字典
    dic = {}
    for b in books:
        dic[b.BOOK] = {
            'BOOK_zh': b.BOOK_zh,  # 中文名称
            'begin_index': b.begin_index  # 起始索引
        }
    
    data = []
    
    # 为每个单词书生成列表信息
    for BOOK, book_info in dic.items():
        book = book_info['BOOK_zh']
        index = book_info['begin_index']
        
        # 获取该单词书的所有列表号
        lists = sorted([
            l[0] for l in (set(Review.objects.filter(BOOK=BOOK).values_list('LIST')))
        ])
        
        list_info = []
        # 处理每个列表
        for l in lists:
            try:
                # 获取列表的BookList记录
                ld = BookList.objects.get(BOOK=BOOK, LIST=l)
            except Exception as e:
                print(f"获取列表 {l} 信息失败: {e}")
                continue
            
            # 计算未掌握和已掌握的单词数量
            if ld.unlearned_num == -1:
                # 未初始化的列表
                L = ld.word_num  # 总单词数
                del_L = 0  # 已掌握数量
            else:
                L = ld.unlearned_num  # 未掌握数量
                del_L = ld.word_num - ld.unlearned_num  # 已掌握数量
            
            # 计算自愿复习次数
            plus = len(ld.review_dates_plus.split(';')) if ld.review_dates_plus != "" else 0
            
            # 添加列表信息
            list_info.append(
                dict(
                    i=l,  # 列表号
                    len=L,  # 未掌握数量
                    del_len=del_L,  # 已掌握数量
                    rate=int(max(0, ld.list_rate) * 100),  # 记忆率（百分比）
                    recent_rate=int(max(0, ld.recent_list_rate) * 100),  # 近期记忆率
                    times=len(ld.review_dates.split(';')) if ld.review_dates != "" else 0,  # 艾宾浩斯复习次数
                    plus='' if plus == 0 else '+' + str(plus),  # 自愿复习次数
                    index=index  # 起始索引
                )
            )
        
        # 添加单词书信息到数据列表
        data.append({'name': book, 'name_en': BOOK, 'lists': list_info})

    # 返回主页，传递数据给模板
    return render(request, "homepage.pug", locals())
