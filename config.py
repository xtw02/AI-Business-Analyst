import os
from openai import OpenAI
import gzip
import shutil


# =========================
# 项目路径
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "business.db"
)

# 云端自动解压数据库
DB_GZIP_PATH = DB_PATH + ".gz"

if not os.path.exists(DB_PATH) and os.path.exists(DB_GZIP_PATH):

    with gzip.open(DB_GZIP_PATH, "rb") as f_in:
        with open(DB_PATH, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

METRICS_PATH = os.path.join(
    BASE_DIR,
    "knowledge",
    "metrics.md"
)


# =========================
# DeepSeek 配置
# =========================

DEEPSEEK_API_KEY = os.environ.get(
    "DEEPSEEK_API_KEY"
)

if not DEEPSEEK_API_KEY:
    raise ValueError(
        "未找到 DEEPSEEK_API_KEY 环境变量。"
        "请先在系统环境变量中配置 API Key。"
    )


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


MODEL_NAME = "deepseek-v4-flash"


# =========================
# 数据库 Schema
# =========================

schema = """
数据库名称：business.db

核心数据表：sales

字段：
- InvoiceNo：订单号
- StockCode：商品编码
- Description：商品名称
- Quantity：购买数量
- InvoiceDate：订单时间
- UnitPrice：商品单价
- CustomerID：用户ID
- Country：国家
- Amount：销售金额，计算方式为 Quantity * UnitPrice

说明：
sales 表只保留正常销售记录，
Quantity > 0，
且 InvoiceNo 不以 C 开头。
"""