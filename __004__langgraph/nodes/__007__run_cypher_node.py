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
from common.neo4j_manager import neo4j_client


def run_cypher_node(state: AgentState):
    print("开始运行大模型cypher语句")
    cypher_query_list = state.get("cypher_query", [])
    query_results = []

    for cypher_query in cypher_query_list:
        result_list = neo4j_client.run_cypher(cypher_query)
        query_results.append({
            "query": cypher_query,
            "result": result_list
        })

    # 存入 state
    state["cypher_results"] = query_results
    print("完成运行大模型cypher语句")
    return state


if __name__ == '__main__':
    result = run_cypher_node({
        "cypher_query": [
            "MATCH (s:Symptom)-[:ALLEVIATES_SYMPTOM]-(f:Formula) WHERE s.name IN ['脑风头痛', '头顶痛', '头风脑痛'] RETURN DISTINCT f.name AS formula_name, f.effect AS effect, f.indication AS indication, f.usage AS usage, f.taboo AS taboo",
            "MATCH (s:Symptom)-[:ALLEVIATES_SYMPTOM]-(h:Herb) WHERE s.name IN ['脑风头痛', '头顶痛', '头风脑痛'] RETURN DISTINCT h.name AS herb_name, h.property_flavor AS property_flavor, h.meridian AS meridian, h.dosage AS dosage, h.usage AS usage, h.taboo AS taboo"]
    })
    print(result["cypher_results"])
