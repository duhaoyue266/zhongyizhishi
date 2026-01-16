from langgraph.constants import START, END
from langgraph.graph import StateGraph

from .agent_state import AgentState
from .nodes.__001__zhongyi_intent_node import zhongyi_intent_node
from .nodes.__002__llm_direct_out_node import llm_direct_out_node
from .nodes.__003__extract_entity_from_user_input_node import extract_entity_from_user_input_node
from .nodes.__004__match_entity_from_neo4j_node import match_entity_from_neo4j_node
from .nodes.__005__generate_neo4j_cypher_node import generate_neo4j_cypher_node
from .nodes.__006__check_cypher_node import check_cypher_node
from .nodes.__007__run_cypher_node import run_cypher_node
from .nodes.__008__neo4j_answer_generate_node import neo4j_answer_generate_node
from common.output_pic_graph_utils import output_pic_graph
from common.path_utils import get_file_path


def build_graph():
    # 定义状态图
    graph = StateGraph(AgentState)
    graph.add_node(zhongyi_intent_node.__name__, zhongyi_intent_node)
    graph.add_node(llm_direct_out_node.__name__, llm_direct_out_node)
    graph.add_node(extract_entity_from_user_input_node.__name__, extract_entity_from_user_input_node)
    graph.add_node(match_entity_from_neo4j_node.__name__, match_entity_from_neo4j_node)
    graph.add_node(generate_neo4j_cypher_node.__name__, generate_neo4j_cypher_node)
    graph.add_node(check_cypher_node.__name__, check_cypher_node)
    graph.add_node(run_cypher_node.__name__, run_cypher_node)
    graph.add_node(neo4j_answer_generate_node.__name__, neo4j_answer_generate_node)
    # 添加边
    graph.add_edge(START, zhongyi_intent_node.__name__)

    def is_zhongyi_intent_condition(state: AgentState):
        if state['is_zhongyi_intent']:
            return extract_entity_from_user_input_node.__name__
        else:
            return llm_direct_out_node.__name__

    graph.add_conditional_edges(zhongyi_intent_node.__name__, is_zhongyi_intent_condition,
                                path_map={
                                    extract_entity_from_user_input_node.__name__: extract_entity_from_user_input_node.__name__,
                                    llm_direct_out_node.__name__: llm_direct_out_node.__name__
                                })
    graph.add_edge(extract_entity_from_user_input_node.__name__, match_entity_from_neo4j_node.__name__)
    graph.add_edge(match_entity_from_neo4j_node.__name__, generate_neo4j_cypher_node.__name__)
    graph.add_edge(generate_neo4j_cypher_node.__name__, check_cypher_node.__name__)

    def is_all_validate_cypher_condition(state: AgentState):
        if state['is_all_validate_cypher']:
            return run_cypher_node.__name__
        else:
            return generate_neo4j_cypher_node.__name__

    graph.add_conditional_edges(check_cypher_node.__name__, is_all_validate_cypher_condition,
                                path_map={
                                    run_cypher_node.__name__: run_cypher_node.__name__,
                                    generate_neo4j_cypher_node.__name__: generate_neo4j_cypher_node.__name__
                                }
                                )
    graph.add_edge(run_cypher_node.__name__, neo4j_answer_generate_node.__name__)
    graph.add_edge(neo4j_answer_generate_node.__name__, END)

    # 编译状态图
    app = graph.compile()
    return app


app = build_graph()
# 输出表的状态图
output_pic_graph(app, get_file_path("__004__langgraph/graph.jpg"))


def zhongyi_response(input: str):
    result = app.invoke({"input": input})
    return result["output"]


if __name__ == '__main__':
    input = "我脑袋疼，我该吃什么药？"
    print(zhongyi_response(input))