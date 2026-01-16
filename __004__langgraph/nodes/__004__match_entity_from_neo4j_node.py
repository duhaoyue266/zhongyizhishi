import faiss
import pickle
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
from common.embedding_model import my_embedding_model

conf = Config()

# 索引和映射的懒加载变量
_index = None
_id2text = None


def _load_index():
    """懒加载索引和映射，仅在需要时加载"""
    global _index, _id2text
    if _index is None or _id2text is None:
        import os
        # 规范化路径，处理混合的路径分隔符
        index_path = os.path.normpath(conf.ENTITY_INDEX_PATH)
        id2text_path = os.path.normpath(conf.ENTITY_ID2TEXT_PATH)
        
        # 检查文件是否存在
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"索引文件不存在: {index_path} (绝对路径: {os.path.abspath(index_path)})")
        if not os.path.exists(id2text_path):
            raise FileNotFoundError(f"映射文件不存在: {id2text_path} (绝对路径: {os.path.abspath(id2text_path)})")
        
        # 检查文件是否可读
        if not os.access(index_path, os.R_OK):
            raise PermissionError(f"索引文件不可读: {index_path}")
        if not os.access(id2text_path, os.R_OK):
            raise PermissionError(f"映射文件不可读: {id2text_path}")
        
        try:
            # 使用绝对路径确保faiss能正确读取
            abs_index_path = os.path.abspath(index_path)
            abs_id2text_path = os.path.abspath(id2text_path)
            
            print(f"正在加载索引文件: {abs_index_path}")
            # 确保路径是字符串格式
            _index = faiss.read_index(str(abs_index_path))
            
            print(f"正在加载映射文件: {abs_id2text_path}")
            with open(str(abs_id2text_path), "rb") as f:
                _id2text = pickle.load(f)
            print("索引和映射文件加载成功")
        except Exception as e:
            raise RuntimeError(f"加载索引文件失败: {e}, 索引路径: {abs_index_path}, 映射路径: {abs_id2text_path}") from e
    return _index, _id2text


def search_faiss(query, top_k=3, threshold=0.65):
    """
    在已有的 FAISS 索引中搜索，并设置相似度阈值
    """
    print("开始从faiss索引搜索")
    
    # 懒加载索引和映射
    index, id2text = _load_index()

    # 生成查询向量
    query_emb = my_embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    # 检索 (返回 L2 距离)
    dists, ids = index.search(query_emb, top_k)

    results = []
    for j, i in enumerate(ids[0]):
        if i == -1:  # 没找到
            continue
        dist = dists[0][j]
        sim = 1.0 - dist / 2.0  # 转换成余弦相似度
        if sim >= threshold:
            results.append({"text": id2text[i], "similarity": float(sim)})
    print("完成从faiss索引搜索")
    return [result['text'] for result in results]


def match_entity_from_neo4j_node(state: AgentState) -> AgentState:
    """
        对六类实体分别在 FAISS 索引中进行匹配搜索：
        - Effect（功效）
        - Disease（疾病）
        - Symptom（症状）
        - Formula（方剂）
        - Herb（药材）
        - Source（出处）
        """
    user_input_effects = state.get("user_input_effects", [])
    user_input_diseases = state.get("user_input_diseases", [])
    user_input_symptoms = state.get("user_input_symptoms", [])
    user_input_formulas = state.get("user_input_formulas", [])
    user_input_herbs = state.get("user_input_herbs", [])
    user_input_sources = state.get("user_input_sources", [])

    matched_effects, matched_diseases, matched_symptoms = [], [], []
    matched_formulas, matched_herbs, matched_sources = [], [], []

    # 分别在 FAISS 中检索
    for eff in user_input_effects:
        matched_effects.extend(search_faiss(eff))

    for dis in user_input_diseases:
        matched_diseases.extend(search_faiss(dis))

    for sym in user_input_symptoms:
        matched_symptoms.extend(search_faiss(sym))

    for form in user_input_formulas:
        matched_formulas.extend(search_faiss(form))

    for herb in user_input_herbs:
        matched_herbs.extend(search_faiss(herb))

    for src in user_input_sources:
        matched_sources.extend(search_faiss(src))

    # 存入 state
    state["matched_effects"] = matched_effects
    state["matched_diseases"] = matched_diseases
    state["matched_symptoms"] = matched_symptoms
    state["matched_formulas"] = matched_formulas
    state["matched_herbs"] = matched_herbs
    state["matched_sources"] = matched_sources

    print("完成实体匹配搜索")
    return state


if __name__ == '__main__':
    print(match_entity_from_neo4j_node(
        {"user_input_effects": [], "user_input_diseases": [], "user_input_symptoms": ["脑袋疼"]}))