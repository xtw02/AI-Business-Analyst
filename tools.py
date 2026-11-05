import sqlite3
import pandas as pd
import json

from config import DB_PATH


# =========================================================
# 1. SQL 安全检查
# =========================================================

def check_sql_safety(sql):
    """
    检查 SQL 是否为安全的只读查询。
    只允许 SELECT / WITH。
    """

    # 去掉 SQL 开头的注释和空白
    lines = sql.strip().splitlines()

    clean_lines = []

    for line in lines:

        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过 -- 单行注释
        if line.startswith("--"):
            continue

        clean_lines.append(line)

    sql_check = " ".join(
        clean_lines
    ).lower().strip()

    # 必须是 SELECT / WITH
    if not (
        sql_check.startswith("select")
        or sql_check.startswith("with")
    ):
        return (
            False,
            "SQL 不安全：只允许 SELECT 查询"
        )

    # 禁止修改数据库
    dangerous_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate"
    ]

    for keyword in dangerous_keywords:

        if keyword in sql_check:

            return (
                False,
                f"SQL 不安全：包含危险操作 {keyword}"
            )

    return True, "SQL 安全"


# =========================================================
# 2. 执行 SQL
# =========================================================

def execute_sql(sql):
    """
    执行 SQL 并返回查询结果。
    """

    # SQL 安全检查
    is_safe, message = check_sql_safety(sql)

    if not is_safe:

        return None, message

    conn = None

    try:

        # 连接数据库
        conn = sqlite3.connect(
            DB_PATH
        )

        # 执行查询
        result = pd.read_sql(
            sql,
            conn
        )

        return (
            result,
            "SQL执行成功"
        )

    except Exception as e:

        return (
            None,
            f"SQL执行失败：{e}"
        )

    finally:

        if conn is not None:
            conn.close()


# =========================================================
# 3. Agent SQL Tool
# =========================================================

def run_sql_tool(sql):
    """
    Agent 调用的 SQL 工具。
    """

    result, message = execute_sql(
        sql
    )

    if result is None:

        return {
            "success": False,
            "message": message
        }

    return {
        "success": True,
        "data": result.to_dict(
            orient="records"
        )
    }


# =========================================================
# 4. 分析计划 Tool
# =========================================================

analysis_plan_tool = {

    "type": "function",

    "function": {

        "name": "set_analysis_plan",

        "description": (
            "制定本次数据分析任务的分析计划。"
            "在执行SQL之前必须先确定分析目标、"
            "核心指标、指标拆解方式、"
            "分析步骤以及停止条件。"
        ),

        "parameters": {

            "type": "object",

            "properties": {

                "goal": {
                    "type": "string",
                    "description": (
                        "本次分析要回答的核心业务问题"
                    )
                },

                "metric": {
                    "type": "string",
                    "description": (
                        "核心分析指标"
                    )
                },

                "decomposition": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": (
                        "核心指标需要拆解的因素"
                    )
                },

                "planned_steps": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": (
                        "计划采用的分析步骤"
                    )
                },

                "stop_condition": {
                    "type": "string",
                    "description": (
                        "什么情况下可以认为证据已经充分，"
                        "并停止继续查询"
                    )
                }
            },

            "required": [
                "goal",
                "metric",
                "decomposition",
                "planned_steps",
                "stop_condition"
            ]
        }
    }
}


# =========================================================
# 5. 结果评估 Tool
# =========================================================

evaluate_result_tool = {

    "type": "function",

    "function": {

        "name": "evaluate_result",

        "description": (
            "评估当前SQL查询结果是否已经足以回答用户问题，"
            "并决定是否需要继续分析。"
        ),

        "parameters": {

            "type": "object",

            "properties": {

                "status": {

                    "type": "string",

                    "enum": [
                        "continue",
                        "finish"
                    ],

                    "description": (
                        "continue表示需要继续查询；"
                        "finish表示当前证据足够"
                    )
                },

                "reason": {

                    "type": "string",

                    "description": (
                        "说明为什么继续分析，"
                        "或者为什么可以结束"
                    )
                },

                "evidence": {

                    "type": "array",

                    "items": {
                        "type": "string"
                    },

                    "description": (
                        "支持当前判断的数据证据，"
                        "例如查询结果中的关键指标、"
                        "排名、数值"
                    )
                },

                "missing_analysis": {

                    "type": "string",

                    "description": (
                        "如果当前证据不足，"
                        "需要说明还缺少哪些分析"
                    )
                },

                "next_action": {

                    "type": "string",

                    "description": (
                        "下一步动作，"
                        "如果finish则说明无需继续查询"
                    )
                }
            },

            "required": [
                "status",
                "reason",
                "evidence",
                "missing_analysis",
                "next_action"
            ]
        }
    }
}


# =========================================================
# 6. Agent 工具集合
# =========================================================

tools_schema = [

    {
        "type": "function",

        "function": {

            "name": "execute_sql",

            "description": (
                "执行只读 SQL 查询，"
                "用于从业务数据库中获取数据。"
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "sql": {

                        "type": "string",

                        "description": (
                            "需要执行的 SELECT 或 WITH SQL 查询语句。"
                        )
                    }
                },

                "required": [
                    "sql"
                ]
            }
        }
    },

    analysis_plan_tool,

    evaluate_result_tool
]