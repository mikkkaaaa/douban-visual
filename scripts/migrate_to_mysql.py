# migrate_to_mysql.py
import pandas as pd
from sqlalchemy import create_engine

# 1. 读取Excel 数据
print("正在读取本地 Excel 数据...")
excel_path = "data/processed/豆瓣读书Top250.xlsx"
df = pd.read_excel(excel_path)

# 2. 配置 MySQL 连接
db_user = "root"
db_password = "123456"  
db_host = "localhost"
db_port = "3306"
db_name = "douban_db"

engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4")

# 3. 一键写入数据库
print("正在将数据导入 MySQL 数据库...")
try:
    # if_exists='replace' 表示如果表已存在就替换它，适合反复调试
    # index=False 表示不要把 pandas 自带的 0,1,2,3 索引写进数据库
    df.to_sql(name="books", con=engine, if_exists="replace", index=False)
    print(f"数据已导入 douban_db 的 books 表中。")
except Exception as e:  
    print(f"导入失败，错误原因：{e}")