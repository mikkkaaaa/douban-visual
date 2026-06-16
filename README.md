# 豆瓣读书 Top250 可视化与 AI 分析平台

这是一个基于 Streamlit、MySQL、Plotly 和 DeepSeek API 的图书数据可视化与 AI 分析项目。项目围绕豆瓣读书 Top250 图书数据，提供公共书库浏览、数据筛选、图表分析、短评情感分析、书籍推荐关系网络、AI 推荐、AI 数据分析、用户登录注册和个人书库管理等功能。

本项目已完成在线部署：代码托管在 GitHub，前端应用部署在 Streamlit Cloud，远程数据库使用 Railway MySQL，线上密钥与数据库连接信息通过 Streamlit Cloud Secrets 管理。

## 项目背景

随着在线阅读平台和图书社区的发展，图书评分、短评、推荐关系和用户阅读记录中包含了大量可分析的信息。本项目以豆瓣读书 Top250 数据为基础，构建一个面向图书数据分析和阅读推荐的 Web 平台。

系统不仅提供基础的图书列表展示和数据可视化，还接入 DeepSeek API，实现 AI 阅读指南、图书推荐和数据分析报告生成。登录用户可以维护个人书库，并将个人书库与公共书库进行统一分析，从而形成一个集数据展示、交互分析和智能辅助决策于一体的图书分析系统。

## 核心功能

- 公共书库浏览：展示豆瓣读书 Top250 图书的书名、评分、作者/出版信息、简介、链接、相关推荐和热门短评。
- 筛选与排序：支持按评分范围、书名/作者关键词、评分、短评热度和出版年份筛选排序。
- 数据可视化：支持评分 Top、热度 Top、评分与热度关系、出版年份趋势、短评情感分析和推荐关系网络图。
- AI 阅读指南：在单本书详情中调用 DeepSeek API，生成简洁的阅读指南。
- AI 推荐：用户输入阅读需求后，AI 基于当前筛选书库进行推荐。
- AI 数据分析：支持公共书库、个人书库、公共书库 + 个人书库的数据分析报告和 AI 图表 Dashboard。
- 用户系统：支持用户注册、登录和退出。
- 个人书库：登录用户可上传 CSV/Excel、手动录入或批量粘贴个人图书数据，并支持查看、修改、删除、清空、导出和基础分析。

## 技术栈

- Streamlit：构建 Web 应用界面、侧边栏、表单、Tabs、图表容器和聊天交互。
- pandas：负责数据读取、清洗、字段统一、统计分析和 CSV 导出。
- Plotly：生成交互式数据可视化图表。
- MySQL：存储公共书库、用户账号和个人书库数据。
- Railway MySQL：线上远程 MySQL 数据库服务。
- SQLAlchemy / PyMySQL：配合 Streamlit SQL connection 访问 MySQL。
- DeepSeek API：提供 AI 阅读指南、图书推荐、AI 数据分析和 AI 图表方案生成。
- OpenAI SDK：使用 OpenAI 兼容接口调用 DeepSeek。
- NetworkX / PyVis：构建并渲染书籍推荐关系网络图。
- SnowNLP：对热门短评进行中文情感倾向分析。
- openpyxl：支持 Excel 文件读取。

## 项目结构

```text
.
├── app.py                         # Streamlit 应用入口
├── requirements.txt               # Python 依赖
├── README.md                      # 项目说明文档
├── assets/
│   ├── style.css                  # 页面样式
│   └── icons/                     # 图标和静态资源
├── components/
│   ├── sidebar.py                 # 公共书库筛选、排序、导出和分页
│   ├── books/
│   │   ├── overview.py            # 书籍总览和单书详情
│   │   └── charts.py              # 数据可视化模块
│   ├── ai/
│   │   ├── prompts.py             # AI Prompt 构造
│   │   ├── curator.py             # AI 推荐模块
│   │   └── data_analyst.py        # AI 数据分析和 AI 图表生成
│   └── user/
│       ├── auth.py                # 登录注册组件
│       └── my_library.py          # 个人书库功能
├── lib/
│   ├── database.py                # 公共图书数据读取
│   ├── ai_client.py               # DeepSeek Client 初始化
│   ├── user_database.py           # 用户表和登录注册逻辑
│   └── user_library_database.py   # 个人书库数据库逻辑
├── utils/
│   ├── book_cleaner.py            # 公共书库字段清洗
│   ├── uploaded_data.py           # 用户上传数据标准化
│   ├── data_unifier.py            # 公共书库和个人书库字段统一
│   ├── sentiment_analyzer.py      # 短评情感分析
│   ├── style_loader.py            # CSS 加载
│   └── icon_loader.py             # SVG 图标加载
└── scripts/
    └── migrate_to_mysql.py        # 本地数据导入 MySQL 的辅助脚本
```

## 在线部署结构

当前项目已经完成部署，部署结构如下：

1. GitHub

   用于保存项目代码。Streamlit Cloud 从 GitHub 仓库拉取代码进行部署。

2. Streamlit Cloud

   用于部署 Streamlit Web 应用。应用入口文件是 `app.py`。

3. Railway MySQL

   用于作为远程 MySQL 数据库，保存公共书库 `books` 表、用户 `users` 表和个人书库 `user_books` 表等数据。

4. Streamlit Secrets

   线上部署时，数据库连接信息和 DeepSeek API Key 都配置在 Streamlit Cloud 的 Secrets 中，而不是写在代码里。

## 数据库连接逻辑

项目代码中使用 Streamlit 的 SQL connection 连接 MySQL：

```python
st.connection("mysql", type="sql")
```

在线部署时，这个连接会读取 Streamlit Cloud Secrets 中的配置。示例配置如下，所有值都应替换为自己的线上配置，占位符不要直接用于生产环境：

```toml
[connections.mysql]
dialect = "mysql"
driver = "pymysql"
host = "your_railway_mysql_host"
port = your_railway_mysql_port
database = "railway"
username = "your_mysql_username"
password = "your_mysql_password"
query = { charset = "utf8mb4" }

DEEPSEEK_API_KEY = "your_deepseek_api_key"
```

注意：Streamlit Cloud 访问 Railway MySQL 时应使用 Railway 提供的公网 MySQL Host 和公网 Port，不要使用 Railway 内部网络地址。

## 数据库表说明

主要数据表包括：

- `books`：公共书库表，保存豆瓣读书 Top250 图书数据，包括书名、链接、作者/出版信息、评分、简介、相关推荐和热门短评等字段。
- `users`：用户表，保存注册用户信息。密码以哈希形式存储，不保存明文密码。
- `user_books`：个人书库表，保存用户上传、粘贴或手动录入的个人图书数据。

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动应用：

```bash
streamlit run app.py
```

本地运行前需要自行配置 Streamlit Secrets，并确保 MySQL 中存在项目所需数据表。不要将本地 secrets 文件提交到 Git。

## 安全与部署注意事项

- 不要把真实 API Key、数据库密码、Railway 密码写入代码或 README。
- 不要将 `.streamlit/secrets.toml`、`.env`、`*.sql` 文件加入 Git。
- 不要修改 `app.py` 的主结构，除非确有必要。
- 不要修改 `lib/database.py` 中的 `st.connection("mysql", type="sql")` 连接逻辑。
- 不要修改 Streamlit Cloud、Railway、GitHub 的部署配置，除非明确需要调整部署。
- README 中所有配置示例均应使用占位符，例如 `your_railway_mysql_host`、`your_mysql_password`、`your_deepseek_api_key`。
- 后续修改代码时，应以保持现有线上部署稳定为前提，优先做小范围、可验证的改动。

## 演示建议

推荐演示流程：

1. 展示公共书库首页和核心指标。
2. 使用侧边栏筛选图书，并展示当前筛选结果。
3. 展示评分 Top、热度 Top、评分与热度关系、出版年份趋势等可视化图表。
4. 运行短评情感分析，说明情感分析结果仅作为辅助判断。
5. 生成书籍推荐关系网络图，展示图书之间的关联关系。
6. 使用 AI 推荐模块输入阅读需求，展示基于当前书库的推荐结果。
7. 登录用户账号，展示个人书库导入、查看、修改和基础分析。
8. 打开 AI 数据分析模块，生成数据分析报告和 AI 图表 Dashboard。

## 项目特点

本项目将图书数据采集、数据库存储、Web 可视化、用户系统和大模型分析能力结合起来，形成了一个完整的图书数据分析平台。相比单纯的数据展示页面，本项目具有更强的交互性、扩展性和智能化能力，适合作为数据可视化、数据库应用和 AI 辅助分析方向的综合实践项目。
