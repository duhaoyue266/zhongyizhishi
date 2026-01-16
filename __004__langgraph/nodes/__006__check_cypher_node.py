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


def check_cypher_node(state:AgentState):
    print("开始检查cypher语句")
    cypher_query_list = state["cypher_query"]
    state['is_all_validate_cypher'] = True
    for cypher_query in cypher_query_list:
        if not neo4j_client.validate_cypher(cypher_query):
            state['is_all_validate_cypher'] = False
            break
    print(f"完成检查cypher语句:{state['is_all_validate_cypher']}")
    return state


if __name__ == '__main__':
    print(check_cypher_node({"cypher_query":["MATCH (e:Employee) RETURN e.id, e.name, e.salary, e.deptno"]}))
    # print(check_cypher_node({"cypher_query":["MATCH (e:Employee) RETU e.id, e.name, e.salary, e.deptno"]}))