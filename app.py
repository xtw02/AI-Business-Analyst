import streamlit as st
from agent import call_agent

# =========================
# 页面配置
# =========================

st.set_page_config(
    page_title="AI 商业分析助手",
    page_icon="📊",
    layout="wide"
)

# =========================
# Session State
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = None


# =========================
# 侧边栏
# =========================

with st.sidebar:

    st.title("📊 AI 商业分析助手")

    st.markdown(
        """
        ### 🤖 系统能力

        - 自然语言业务分析
        - RAG 指标知识检索
        - Text2SQL
        - Agent 自动分析
        - SQL 安全校验
        - 多轮追问
        - 分析过程可解释

        ### 💡 示例问题

        **基础分析**

        - 哪个国家的销售额最高？
        - 英国的销售额是多少？
        - 哪个国家订单量最高？

        **拆解分析**

        - 英国销售额为什么最高？
        - 英国销售额高是因为客户多还是下单次数多？
        - 英国的客单价是多少？

        **连续追问**

        - 哪个国家销售额最高？
        - 为什么？
        - 它的客单价是多少？
        """
    )

    st.divider()

    if st.button("🗑️ 清空对话", use_container_width=True):

        st.session_state.messages = []
        st.session_state.memory = None

        st.rerun()


# =========================
# 主页面
# =========================

st.title("📊 AI 商业分析助手")

st.caption(
    "基于 RAG + Text2SQL + Agent 的智能业务分析系统"
)

st.divider()


# =========================
# 欢迎页
# =========================

if len(st.session_state.messages) == 0:

    st.markdown(
        """
        ## 👋 你好，我是 AI 商业分析助手

        你可以直接用自然语言提问，我会自动完成：

        **业务问题 → 分析计划 → SQL 查询 → 数据验证 → 分析结论**

        例如：

        > 英国销售额为什么最高？

        我会进一步拆解客户数量、订单数量、客单价等因素。
        """
    )


# =========================
# 历史对话
# =========================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Assistant 的分析过程
        if message["role"] == "assistant":

            result = message.get("result")

            if result:

                with st.expander("🔎 查看分析过程"):

                    # -------------------------
                    # 分析计划
                    # -------------------------

                    plans = result.get("plans", [])

                    if plans:

                        st.markdown("### 🧠 分析计划")

                        for i, plan in enumerate(plans, 1):

                            st.markdown(f"**步骤 {i}**")

                            st.json(plan)

                    # -------------------------
                    # RAG 检索结果
                    # -------------------------

                    rag_results = result.get(
                        "rag_results",
                        []
                    )

                    if rag_results:

                        st.markdown("### 📚 RAG 知识检索")

                        for i, item in enumerate(
                            rag_results,
                            1
                        ):

                            st.markdown(
                                f"**知识片段 {i}** "
                                f"(相似度：{item.get('score', 0):.3f})"
                            )

                            st.write(
                                item.get("chunk", "")
                            )

                    # -------------------------
                    # SQL
                    # -------------------------

                    sql_queries = result.get(
                        "sql_queries",
                        []
                    )

                    if sql_queries:

                        st.markdown("### 🗄️ SQL 查询")

                        for i, item in enumerate(
                            sql_queries,
                            1
                        ):

                            st.markdown(
                                f"**SQL {i}**"
                            )

                            st.code(
                                item.get("sql", ""),
                                language="sql"
                            )

                            sql_result = item.get(
                                "result"
                            )

                            if sql_result:

                                st.markdown(
                                    "**查询结果**"
                                )

                                st.dataframe(
                                    sql_result,
                                    use_container_width=True
                                )

                    # -------------------------
                    # Agent Evaluation
                    # -------------------------

                    evaluations = result.get(
                        "evaluations",
                        []
                    )

                    if evaluations:

                        st.markdown(
                            "### 🔄 Agent 结果评估"
                        )

                        for i, evaluation in enumerate(
                            evaluations,
                            1
                        ):

                            st.markdown(
                                f"**评估 {i}**"
                            )

                            st.json(evaluation)


# =========================
# 用户输入
# =========================

question = st.chat_input(
    "请输入你的业务问题，例如：英国销售额为什么最高？"
)


# =========================
# 调用 Agent
# =========================

if question:

    # 保存用户消息
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    # 显示用户问题
    with st.chat_message("user"):

        st.markdown(question)

    # Agent
    with st.chat_message("assistant"):

        with st.spinner(
            "🤖 Agent 正在分析数据..."
        ):

            try:

                result = call_agent(
                    question,
                    memory=st.session_state.memory
                )

                answer = result.get(
                    "answer",
                    "暂时无法生成分析结果。"
                )

                # -------------------------
                # 显示答案
                # -------------------------

                st.markdown(answer)

                # -------------------------
                # 更新 Memory
                # -------------------------

                st.session_state.memory = result.get(
                    "memory"
                )

                # -------------------------
                # 分析过程
                # -------------------------

                with st.expander(
                    "🔎 查看分析过程"
                ):

                    plans = result.get(
                        "plans",
                        []
                    )

                    if plans:

                        st.markdown(
                            "### 🧠 分析计划"
                        )

                        for i, plan in enumerate(
                            plans,
                            1
                        ):

                            st.markdown(
                                f"**步骤 {i}**"
                            )

                            st.json(plan)

                    rag_results = result.get(
                        "rag_results",
                        []
                    )

                    if rag_results:

                        st.markdown(
                            "### 📚 RAG 知识检索"
                        )

                        for i, item in enumerate(
                            rag_results,
                            1
                        ):

                            st.markdown(
                                f"**知识片段 {i}** "
                                f"(相似度：{item.get('score', 0):.3f})"
                            )

                            st.write(
                                item.get("chunk", "")
                            )

                    sql_queries = result.get(
                        "sql_queries",
                        []
                    )

                    if sql_queries:

                        st.markdown(
                            "### 🗄️ SQL 查询"
                        )

                        for i, item in enumerate(
                            sql_queries,
                            1
                        ):

                            st.markdown(
                                f"**SQL {i}**"
                            )

                            st.code(
                                item.get("sql", ""),
                                language="sql"
                            )

                            sql_result = item.get(
                                "result"
                            )

                            if sql_result:

                                st.markdown(
                                    "**查询结果**"
                                )

                                st.dataframe(
                                    sql_result,
                                    use_container_width=True
                                )

                    evaluations = result.get(
                        "evaluations",
                        []
                    )

                    if evaluations:

                        st.markdown(
                            "### 🔄 Agent 结果评估"
                        )

                        for i, evaluation in enumerate(
                            evaluations,
                            1
                        ):

                            st.markdown(
                                f"**评估 {i}**"
                            )

                            st.json(evaluation)

                # -------------------------
                # 保存完整结果
                # -------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "result": result
                    }
                )

            except Exception as e:

                st.error(
                    "❌ Agent 运行失败"
                )

                st.exception(e)