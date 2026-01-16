import json
import sys
from pathlib import Path

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
from common.config import Config
from langchain_core.messages import HumanMessage
from common.llm import my_llm

conf = Config()


def generate_neo4j_cypher_node(state: AgentState) -> AgentState:
    print("开始生成neo4j的cypher语句")

    user_input = state["input"]

    # 从 state 取出所有匹配到的实体
    matched_effects = state.get("matched_effects", [])
    matched_diseases = state.get("matched_diseases", [])
    matched_symptoms = state.get("matched_symptoms", [])
    matched_formulas = state.get("matched_formulas", [])
    matched_herbs = state.get("matched_herbs", [])
    matched_sources = state.get("matched_sources", [])

    meta_data = conf.TCM_METADATA  # 知识图谱元数据（节点、关系定义等）

    # # 格式化匹配到的实体，确保只保留文本内容
    # def format_entities(entities):
    #     if isinstance(entities, list):
    #         return [e["text"] if isinstance(e, dict) else str(e) for e in entities]
    #     return []
    #
    # effects_list = format_entities(matched_effects)
    # diseases_list = format_entities(matched_diseases)
    # symptoms_list = format_entities(matched_symptoms)
    # formulas_list = format_entities(matched_formulas)
    # herbs_list = format_entities(matched_herbs)
    # sources_list = format_entities(matched_sources)

    # 构建提示词
    prompt = f"""
    你是一个 Neo4j Cypher 查询语句生成助手。
    请基于中医知识图谱，结合用户输入和已匹配实体，生成最合适的查询语句。

    用户输入：{user_input}

    匹配到的实体：
    - effects（功效）: {matched_effects}
    - diseases（疾病）: {matched_diseases}
    - symptoms（症状）: {matched_symptoms}
    - formulas（方剂）: {matched_formulas}
    - herbs（药材）: {matched_herbs}
    - sources（出处）: {matched_sources}

    知识图谱元数据（节点与关系定义）：
    {meta_data}

    要求：
    1. 根据用户输入语义、匹配到的实体及元数据，生成 1~N 条合适的 Cypher 查询。
    2. 输出必须是严格的 JSON 格式：
    {{
        "cypher": [
            "MATCH ... RETURN ...",
            "MATCH ... RETURN ..."
        ]
    }}
    3. 不得包含任何解释或额外文字。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    raw_output = response.content.strip()

    try:
        cypher_data = json.loads(raw_output)
    except json.JSONDecodeError:
        cypher_data = {"cypher": []}

    # 保存结果到 state
    state["cypher_query"] = cypher_data.get("cypher", [])

    print(f"完成生成neo4j的cypher语句{state['cypher_query']}")
    return state


if __name__ == "__main__":
    state = AgentState()
    state["input"] = "我脑袋疼该吃什么药？"
    state["matched_symptoms"] = ["脑风头痛", "头顶痛", "头风脑痛"]
    result = generate_neo4j_cypher_node(state)
    print(result["cypher_query"])