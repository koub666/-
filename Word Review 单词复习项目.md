# Word Review 单词复习项目

基于 Django 开发的单词复习应用，依托艾宾浩斯遗忘曲线实现科学记忆，支持自定义单词列表、复习计划可视化、多单词书适配等核心功能，将传统「Excel 背单词」数字化、便捷化。

## 一、项目简介

### 1.1 项目背景

灵感源于知乎红专学姐背单词方法及 B 站相关分享，针对传统背单词方式效率低、复习无规律的问题，通过数字化工具重构背单词流程，适配现代用户操作习惯。

### 1.2 核心价值

- 科学记忆：基于艾宾浩斯遗忘曲线自动生成复习计划

- 个性化适配：支持托福、考研、初高中等多单词书，可自定义列表

- 直观反馈：记忆曲线可视化，实时展示复习进度与记忆率

- 高效便捷：支持快捷键操作，支持本地部署保护隐私

## 二、核心功能

1. **单词复习核心**：单词卡片展示、记忆状态标记（记得/不认识）、单词分类（重难词/已掌握等）、快捷键支持

2. **艾宾浩斯复习日历**：自动生成复习计划、日历可视化每日复习清单、跟踪复习次数与记忆率

3. **昨日重现**：自动筛选昨日复习单词、随机排序复习、展示复习进度

4. **单词列表管理**：多单词书支持、列表进度可视化、区分学习/复习状态

5. **记忆曲线可视化**：历史记忆率统计、复习后实时更新、ECharts 图表直观展示

## 三、技术栈

|分类|技术|版本|
|---|---|---|
|后端框架|Django|3+|
|编程语言|Python|3.7+|
|数据库|MySQL / SQLite|8 / 3|
|前端模板|Pug|-|
|CSS 框架|Bootstrap|-|
|JavaScript 库|jQuery|3.5.1|
|图表库|ECharts|-|
|部署方式|WSGI / ASGI|-|
## 四、安装与部署

### 4.1 前置准备

1. 确保Python 3.7+已安装

2. （可选）创建虚拟环境：

```bash

conda create -n word python=3
conda activate word  # Windows
# 或
source activate word  # Linux/macOS
```

### 4.2 依赖安装

```bash

# 方法1：使用requirements.txt（推荐）
pip install -r requirements.txt

# 方法2：小白流程
pip install django pypugjs pymysql django-compressor django-sass-processor libsass mysqlclient -i http://mirrors.aliyun.com/pypi/simple/
```

### 4.3 数据库配置

- 默认使用SQLite （无需额外配置）：

```bash

# 配置文件中已默认设置
db_type = sqlite
```

- 使用MySQL （可选）：

1. 安装MySQL并创建数据库：

```bash

create database tg_word_db character set utf8;
create user 'tg_word_user'@'localhost' identified by 'tg_word2020';
grant all privileges ON tg_word_db.* TO 'tg_word_user'@'localhost';
flush privileges;
```

2. 修改 config.conf ：

```bash

db_type = mysql
```

### 4.4 数据库迁移

```bash

python manage.py makemigrations
python manage.py migrate
```

### 4.5 启动服务器

```bash

python manage.py runserver
```

### 4.6 导入单词数据

- 运行 import_vocabulary.py 脚本或使用管理命令

- 参考 database_init.md 文档（如果存在）

### 4.7 可能遇到的问题及解决方案

#### 4.7.1 MySQL客户端版本问题

- 错误： mysqlclient 1.3.13 or newer is required

- 解决方案：注释掉Django中的版本检查

```bash

# 在site-packages/django/db/backends/mysql/base.py中注释：
# if version < (1, 3, 13):
#     raise ImproperlyConfigured('mysqlclient 1.3.13 or newer is required; you have %s.' % Database.__version__)
```

#### 4.7.2 虚拟环境问题

- 如果不使用虚拟环境，可能会出现依赖冲突

- 建议使用虚拟环境隔离项目依赖

#### 4.7.3 数据库连接问题

- 确保MySQL服务已启动

- 检查 config.conf 中的数据库配置是否正确

### 4.8 验证安装成功

- 服务器启动后，访问 http://127.0.0.1:8000/

- 能看到单词复习主页，说明安装成功

- 可以尝试点击"昨日重现"或其他单词列表，验证功能是否正常

## 五、项目目录结构

```plaintext

WordReview/
├── WordReview/           # Django 项目核心配置
│   ├── settings.py       # 项目全局设置
│   ├── urls.py           # 主 URL 路由配置
│   └── wsgi.py           # WSGI 部署配置
├── apps/
│   └── review/           # 核心业务应用
│       ├── models.py     # 数据模型（单词书、单词、复习记录等）
│       ├── views.py      # 视图函数与 API 接口
│       ├── urls.py       # 应用内 URL 配置
│       ├── templates/    # 页面模板（主页、复习页、日历页）
│       └── management/   # 自定义管理命令
├── static/               # 静态资源
│   ├── css/              # 样式文件
│   ├── js/               # 前端逻辑（复习、日历渲染等）
│   └── media/            # 媒体文件
├── templates/            # 全局公共模板
├── manage.py             # Django 命令行工具
└── config.py             # 项目自定义配置
```

## 六、核心数据模型

- Books：存储单词书基本信息（名称、类型等）

- BookList：单词书对应的单词列表（关联 Books）

- Words：单词详情（单词、释义、例句等）

- Review：用户复习记录（单词、复习次数、记忆率、下次复习时间等）

## 七、核心使用流程

### 7.1 单词复习流程

1. 访问主页（http://127.0.0.1:8000/）

2. 选择目标单词书及列表，进入复习页（/review/review?list=X&book=Y）

3. 系统加载单词卡片，展示单词及历史记忆曲线

4. 标记单词状态（记得/不认识），系统自动更新记忆记录

5. 根据艾宾浩斯曲线生成下次复习时间，进入下一个单词

### 7.2 昨日重现流程

1. 点击主页「昨日重现」按钮（/review/review?limit=50）

2. 系统筛选昨日复习单词并随机排序

3. 按正常复习流程完成复习，更新记忆状态

## 八、已解决关键问题

- URL 编码问题：解决中文单词书名称在 URL 中传递的乱码问题

- 数据库查询异常：优化 review_a_word() 函数，避免索引越界错误

- 空词汇列表：优化单词书名称映射与查询逻辑，修复中文单词书空列表问题

- 记忆曲线渲染：修复前端渲染逻辑，确保空历史数据正常展示

## 九、当前状态与未来规划

### 9.1 当前状态

- 核心功能全部实现并正常运行

- 开发服务器可稳定启动（http://127.0.0.1:8000/）

- 代码通过基础语法与功能检查

### 9.2 未来迭代方向

- 功能优化：新增单词学习模式、移动端适配、数据导出、多用户认证

- 性能提升：数据库查询优化、前端资源压缩、添加缓存策略

- 技术升级：Django 版本更新、前端框架现代化（Vue/React）、RESTful API 规范化

- 体验增强：详细统计报表、个性化推荐、学习社交功能

## 十、核心文件说明

|文件路径|功能说明|
|---|---|
|apps/review/views.py|核心视图函数与 API 接口（单词加载、复习记录更新等）|
|apps/review/models.py|数据模型定义（单词书、单词、复习记录等）|
|static/js/review.js|复习页面前端逻辑（卡片渲染、记忆曲线绘制）|
|static/js/calendar.js|艾宾浩斯日历渲染与复习计划展示逻辑|
|apps/review/templates/|页面模板（homepage.pug 主页、review.pug 复习页）|
|WordReview/settings.py|Django 项目全局配置|
## 十一、总结

本项目通过 Django 框架实现了基于艾宾浩斯遗忘曲线的科学背单词工具，解决了传统背单词效率低、复习无规律的痛点。项目结构清晰、功能完整，支持本地部署保障隐私，具备良好的可扩展性与维护性，可满足不同用户的单词记忆需求。