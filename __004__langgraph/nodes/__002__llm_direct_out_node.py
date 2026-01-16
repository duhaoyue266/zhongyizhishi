from langchain_core.messages import HumanMessage
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
from common.llm import my_llm


def llm_direct_out_node(state: AgentState):
    print("开始生成直接用户回答")
    # 获取用户输入
    user_input = state["input"]

    # 构建提示词（专注中医回答）
    prompt = f"""
    用户输入: {user_input}

    你是一名专业的中医知识助手，回答时请尽量基于中医理论和术语来解释。  
    要求：
    - 优先从中医角度（如症状、方剂、中药材、功效、经络、辨证论治、典籍等）进行回答。  
    - 如果问题与中医无关，也尽量从中医的视角进行回答。
    - 回答要准确、简洁，避免无关内容。  
    - 输出时只给出最终答案，不要解释你是如何推理的。
    """

    # 调用大模型
    response = my_llm.invoke([HumanMessage(content=prompt)])
    model_answer = response.content.strip()

    # 存入 state
    state["direct_out"] = model_answer
    state["output"] = model_answer
    print("完成生成直接用户回答")
    return state


if __name__ == '__main__':
    result = llm_direct_out_node({"input": "解释一下欧姆定律。"})
    print(result["output"])
