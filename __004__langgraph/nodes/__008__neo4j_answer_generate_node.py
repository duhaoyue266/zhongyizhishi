import json
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage

# 支持相对导入和直接运行
try:
    from ..agent_state import AgentState
except ImportError:
    # 直接运行时，添加项目根目录和父目录到路径
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import agent_state
    AgentState = agent_state.AgentState
from common.llm import my_llm


def neo4j_answer_generate_node(state: AgentState) -> AgentState:
    print("开始进行neo4j输入大模型的回答")
    user_input = state["input"]
    cypher_results = state.get("cypher_results", [])

    # 把 cypher_results 转成字符串，方便喂给大模型
    cypher_results_str = json.dumps(cypher_results, ensure_ascii=False, indent=2)

    prompt = f"""
    你是一个中医知识图谱问答助手。
    用户提出了问题：{user_input}

    我已经在 Neo4j 图数据库中执行了查询，查询结果如下：
    {cypher_results_str}

    请你根据这些查询结果，用简洁、清晰、自然的中文回答用户的问题。
    如果查询结果无法回答用户的问题，请如实告知用户没有找到相关答案。
    """
    # print(prompt)
    response = my_llm.invoke([HumanMessage(content=prompt)])

    # 保存结果
    state["neo4j_answer"] = response.content.strip()
    state["output"] = response.content.strip()
    print("完成进行neo4j输入大模型的回答")

    return state
