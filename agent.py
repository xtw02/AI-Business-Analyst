import json

from config import (
    client,
    MODEL_NAME,
    schema
)

from rag import retrieved_knowledge

from tools import (
    run_sql_tool,
    tools_schema
)


# =========================================================
# Agent 主函数
# =========================================================

def call_agent(
    user_question,
    memory=None
):
    """
    AI Business Analyst Agent

    流程：

    用户问题
        ↓
    RAG
        ↓
    分析计划
        ↓
    SQL 查询
        ↓
    结果评估
        ↓
    继续分析 / 结束
        ↓
    最终答案
    """

    # =====================================================
    # 1. 初始化 Memory
    # =====================================================

    if memory is None:
        memory = []


    # =====================================================
    # 2. Agent 运行日志
    # =====================================================

    sql_queries = []

    plans = []

    evaluations = []


    # =====================================================
    # 3. RAG 检索
    # =====================================================

    rag_results = retrieved_knowledge(
        user_question,
        top_k=3
    )

    rag_knowledge = "\n\n".join(
        [
            f"【知识块 {i + 1}】\n{result['chunk']}"
            for i, result in enumerate(
                rag_results
            )
        ]
    )


    # =====================================================
    # 4. 初始化消息
    # =====================================================

    messages = [

        {
            "role": "system",

            "content": f"""
你是一个数据分析 Agent。

数据库结构：

{schema}

你可以使用以下工具：

1. set_analysis_plan
制定本次分析计划。

2. execute_sql
执行只读 SQL 查询。

3. evaluate_result
评估当前 SQL 查询结果是否已经足够回答用户问题。

以下是根据用户问题从业务指标知识库中检索到的相关知识：

{rag_knowledge}

你的分析原则：

1. 在执行 SQL 之前，必须先调用 set_analysis_plan。
2. 制定计划后，再调用 execute_sql。
3. 每次获得 SQL 查询结果后，都必须调用 evaluate_result。
4. 如果 evaluate_result 返回 continue，则继续分析并执行下一步 SQL。
5. 如果 evaluate_result 返回 finish，则停止继续查询并生成最终答案。
6. 如果用户询问“为什么”“原因”“下降原因”等问题，不能只报告现象，必须继续寻找影响因素。
7. 根据指标的业务逻辑选择合理的拆解维度。
8. 每一步分析都必须基于数据库真实结果。
9. 如果数据不足以支持某个结论，不要自行推测。
10. 最终按照“现象 → 原因 → 数据证据 → 建议”的结构回答。
11. 每一个原因都必须有查询结果直接支持。
12. 不允许根据国家、行业、数据分布等信息自行推测业务背景。
13. 如果数据只能证明相关，不能证明因果，必须明确说明“只能说明相关，无法确认因果”。
14. 不要自行创造没有依据的样本量阈值或业务规则。
15. 不要编造数据或业务事实。
16. evaluate_result 时必须提供 evidence 字段，列出支持当前判断的查询结果证据。
17. evidence 中的信息必须来自 SQL 查询结果，不允许自行推测。
"""
        }
    ]


    # =====================================================
    # 5. 加入历史对话
    # =====================================================

    for item in memory:

        # -----------------------------------------------
        # 上一轮用户问题
        # -----------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": item["user"]
            }
        )


        # -----------------------------------------------
        # 上一轮 Agent 最终回答
        # -----------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": item["assistant"]
            }
        )


        # -----------------------------------------------
        # 上一轮 SQL 查询结果
        # -----------------------------------------------

        if item.get("sql_queries"):

            sql_context = "\n\n".join(
                [
                    (
                        f"SQL：\n{q['sql']}\n"
                        f"查询结果：\n{q['data']}"
                    )
                    for q in item["sql_queries"]
                ]
            )

            messages.append(
                {
                    "role": "assistant",

                    "content": f"""
这是上一轮分析过程中真实执行过的 SQL 和查询结果：

{sql_context}

这些数据来自数据库真实查询结果，
可以作为后续问题的历史证据。
"""
                }
            )


    # =====================================================
    # 6. 加入当前问题
    # =====================================================

    messages.append(
        {
            "role": "user",
            "content": user_question
        }
    )


    # =====================================================
    # 7. 分析计划状态
    # =====================================================

    analysis_plan = None


    # =====================================================
    # 8. Agent 循环
    # =====================================================

    while True:

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=messages,

            tools=tools_schema,

            tool_choice="auto",

            stream=False,

            extra_body={
                "thinking": {
                    "type": "disabled"
                }
            }
        )


        assistant_message = (
            response.choices[0].message
        )


        # =================================================
        # 9. 没有工具调用
        # =================================================

        if not assistant_message.tool_calls:

            answer = (
                assistant_message.content
            )


            # ---------------------------------------------
            # 保存本轮 Memory
            # ---------------------------------------------

            memory.append(
                {
                    "user": user_question,

                    "assistant": answer,

                    "sql_queries": sql_queries,

                    "plans": plans,

                    "evaluations": evaluations
                }
            )


            # ---------------------------------------------
            # 返回结果
            # ---------------------------------------------

            return {

                "answer": answer,

                "sql_queries": sql_queries,

                "plans": plans,

                "evaluations": evaluations,

                "rag_results": rag_results,

                "memory": memory
            }


        # =================================================
        # 10. 保存 Assistant 工具调用
        # =================================================

        messages.append(
            {
                "role": "assistant",

                "content": (
                    assistant_message.content
                    or ""
                ),

                "tool_calls": [

                    {
                        "id": tc.id,

                        "type": "function",

                        "function": {

                            "name": tc.function.name,

                            "arguments": (
                                tc.function.arguments
                            )
                        }
                    }

                    for tc in assistant_message.tool_calls
                ]
            }
        )


        # =================================================
        # 11. 处理工具调用
        # =================================================

        for tc in assistant_message.tool_calls:

            tool_name = (
                tc.function.name
            )

            arguments = json.loads(
                tc.function.arguments
            )


            # =================================================
            # 工具一：制定分析计划
            # =================================================

            if tool_name == "set_analysis_plan":

                analysis_plan = arguments

                plans.append(
                    analysis_plan
                )


                print(
                    "\n===== Agent 分析计划 ====="
                )

                print(
                    "分析目标：",
                    analysis_plan["goal"]
                )

                print(
                    "核心指标：",
                    analysis_plan["metric"]
                )

                print(
                    "指标拆解：",
                    analysis_plan["decomposition"]
                )

                print(
                    "分析步骤：",
                    analysis_plan["planned_steps"]
                )

                print(
                    "停止条件：",
                    analysis_plan["stop_condition"]
                )


                messages.append(
                    {
                        "role": "tool",

                        "tool_call_id": tc.id,

                        "content": json.dumps(
                            {
                                "success": True,

                                "message": (
                                    "分析计划已确认，"
                                    "可以开始执行 SQL。"
                                )
                            },

                            ensure_ascii=False
                        )
                    }
                )


            # =================================================
            # 工具二：执行 SQL
            # =================================================

            elif tool_name == "execute_sql":

                # 必须先制定分析计划
                if analysis_plan is None:

                    tool_result = {
                        "success": False,

                        "error": (
                            "必须先制定分析计划，"
                            "再执行 SQL。"
                        )
                    }

                else:

                    sql = arguments["sql"]


                    print(
                        "\n===== Agent 调用工具 ====="
                    )

                    print(
                        "工具：",
                        tool_name
                    )

                    print(
                        "SQL："
                    )

                    print(sql)


                    # 执行 SQL
                    tool_result = run_sql_tool(
                        sql
                    )


                    # 保存 SQL 日志
                    sql_queries.append(
                        {
                            "sql": sql,

                            "success": (
                                tool_result["success"]
                            ),

                            "data": (
                                tool_result.get(
                                    "data",
                                    []
                                )
                            )
                        }
                    )


                    print(
                        "\n===== SQL 查询结果 ====="
                    )

                    print(tool_result)


                # 把工具结果返回给 LLM
                messages.append(
                    {
                        "role": "tool",

                        "tool_call_id": tc.id,

                        "content": json.dumps(
                            tool_result,
                            ensure_ascii=False
                        )
                    }
                )


            # =================================================
            # 工具三：结果评估
            # =================================================

            elif tool_name == "evaluate_result":

                evaluation = arguments

                evaluations.append(
                    evaluation
                )


                print(
                    "\n===== Agent 结果评估 ====="
                )

                print(
                    "评估结果：",
                    evaluation["status"]
                )

                print(
                    "评估原因：",
                    evaluation["reason"]
                )

                print(
                    "下一步：",
                    evaluation["next_action"]
                )

                print(
                    "证据：",
                    evaluation.get(
                        "evidence",
                        []
                    )
                )


                # -----------------------------------------
                # finish
                # -----------------------------------------

                if evaluation["status"] == "finish":

                    messages.append(
                        {
                            "role": "tool",

                            "tool_call_id": tc.id,

                            "content": json.dumps(
                                {
                                    "success": True,

                                    "status": "finish",

                                    "message": (
                                        "证据已经足够，"
                                        "请停止继续查询并生成最终答案。"
                                    )
                                },

                                ensure_ascii=False
                            )
                        }
                    )


                # -----------------------------------------
                # continue
                # -----------------------------------------

                else:

                    messages.append(
                        {
                            "role": "tool",

                            "tool_call_id": tc.id,

                            "content": json.dumps(
                                {
                                    "success": True,

                                    "status": "continue",

                                    "message": (
                                        "证据不足，"
                                        "请根据下一步分析计划继续查询。"
                                    ),

                                    "next_action": (
                                        evaluation["next_action"]
                                    )
                                },

                                ensure_ascii=False
                            )
                        }
                    )