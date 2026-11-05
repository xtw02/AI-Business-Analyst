print("START")

from agent import call_agent

print("AGENT IMPORTED")


# ============================================================
# 第一轮：找销售额最高的国家
# ============================================================

print("\n")
print("=" * 70)
print("========== 第一轮：哪个国家的销售额最高？ ==========")
print("=" * 70)

r1 = call_agent(
    "Which country has the highest sales?"
)

print("\n【第一轮最终回答】")
print(r1["answer"])

print("\n【第一轮 SQL】")
for item in r1["sql_queries"]:
    print(item)

print("\n【第一轮 Memory】")
for item in r1["memory"]:
    print(item)


# ============================================================
# 第二轮：为什么它最高？
# ============================================================

print("\n")
print("=" * 70)
print("========== 第二轮：为什么它的销售额最高？ ==========")
print("=" * 70)

r2 = call_agent(
    "Why is it the highest?",
    memory=r1["memory"]
)

print("\n【第二轮最终回答】")
print(r2["answer"])

print("\n【第二轮 SQL】")
for item in r2["sql_queries"]:
    print(item)

print("\n【第二轮 Memory】")
for item in r2["memory"]:
    print(item)


# ============================================================
# 第三轮：它的客单价是多少？
# ============================================================

print("\n")
print("=" * 70)
print("========== 第三轮：那它的客单价是多少？ ==========")
print("=" * 70)

r3 = call_agent(
    "What is its average order value?",
    memory=r2["memory"]
)

print("\n【第三轮最终回答】")
print(r3["answer"])

print("\n【第三轮 SQL】")
for item in r3["sql_queries"]:
    print(item)


# ============================================================
# 最终检查
# ============================================================

print("\n")
print("=" * 70)
print("========== Memory 测试完成 ==========")
print("=" * 70)

print("\n【最终 Memory】")
for item in r3["memory"]:
    print(item)

print("\nSTART → 第一轮完成")
print("第一轮 Memory → 第二轮")
print("第二轮 Memory → 第三轮")
print("测试结束")