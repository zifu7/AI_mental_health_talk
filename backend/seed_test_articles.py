"""插入 3 篇测试文章（本地库没有正式语料时，用于跑通 RAG 链路）

运行方式（在 backend 目录下）：
    venv/Scripts/python seed_test_articles.py
"""
import pymysql

# 主题对应 test_rag.py 里的测试问题（失眠 / 考试焦虑 / 抑郁症）
ARTICLES = [
    ("失眠的常见原因与缓解方法",
     "失眠是很多人都会遇到的情况，通常与压力、焦虑、作息紊乱有关。\n\n"
     "缓解失眠的常用方法：第一，固定入睡和起床时间，养成生物钟；第二，睡前一到两小时避免使用手机等电子设备；"
     "第三，白天进行适量运动，但不要在睡前剧烈运动；第四，睡前可以尝试腹式呼吸或听轻音乐放松。\n\n"
     "如果失眠持续超过两周，并伴随白天精力严重下降、情绪低落，建议尽快寻求专业心理帮助或就医。"),
    ("如何应对考试焦虑",
     "考试焦虑是一种常见的情绪反应，表现为考前紧张、心慌、注意力难以集中，适度焦虑能提升表现，过度焦虑反而影响发挥。\n\n"
     "应对方法：一、制定复习计划，把大目标拆成每天的小任务，减少未知感；二、考前做模拟练习，熟悉考试节奏；"
     "三、考场上如果心慌，先做几次深呼吸，把注意力拉回题目本身；四、提前调整作息，保证考前一周睡眠充足。\n\n"
     "记住，考试只是检验学习成果的一种方式，一次考试的结果不能定义你的价值。"),
    ("了解抑郁症：常见症状与求助途径",
     "抑郁症是一种常见的心理疾病，不是简单的“心情不好”。常见症状包括：持续两周以上的情绪低落、对原本喜欢的事情失去兴趣、"
     "精力减退、睡眠和食欲改变、自我评价下降，严重时会出现轻生念头。\n\n"
     "如果自己或身边的人出现这些症状，建议：第一，尽快寻求专业帮助，到正规医院的心理科或精神科就诊；"
     "第二，与信任的家人朋友沟通，不独自承受；第三，坚持规范治疗，抑郁症是可以治愈的。\n\n"
     "请记住：需要帮助不是软弱，及时求助是勇敢的表现。"),
]

conn = pymysql.connect(
    host="localhost", port=3306, user="root", password="123456",
    database="psychology_db", charset="utf8mb4",
)
cur = conn.cursor()
inserted = 0
for title, content in ARTICLES:
    cur.execute("SELECT COUNT(*) FROM knowledge_articles WHERE title = %s", (title,))
    if cur.fetchone()[0]:
        print(f"已存在，跳过：{title}")
        continue
    cur.execute(
        "INSERT INTO knowledge_articles (title, content, category_id, author_id, status, published_at) "
        "VALUES (%s, %s, 1, 1, 1, NOW())",
        (title, content),
    )
    inserted += 1
conn.commit()
conn.close()
print(f"完成，新插入 {inserted} 篇测试文章")
