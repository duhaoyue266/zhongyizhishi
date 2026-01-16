import json
from common.neo4j_manager import neo4j_client
from common.path_utils import get_file_path
from tqdm import tqdm


def load_json_data(json_path):
    """加载 JSON 文件"""
    print(f"正在加载文件: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def parse_entities_and_relations(data):
    """
    解析 JSON 数据，提取所有实体和关系
    返回: (entities_dict, relations_list)
    entities_dict: {entity_key: {name, type, attributes}}
    relations_list: [{subject, subject_type, relation, object, object_type}]
    """
    entities_dict = {}  # 使用字典去重，key 为 (name, type)
    relations_list = []
    
    for result in tqdm(data.get("results", []), desc="解析数据"):
        extract_dict = result.get("extract_dict", {})
        
        # 解析实体
        for entity in extract_dict.get("entities", []):
            name = entity.get("name")
            entity_type = entity.get("type")
            # 确保 attributes 是字典，如果为 None 或不存在则设为空字典
            attributes = entity.get("attributes") or {}
            if not isinstance(attributes, dict):
                attributes = {}
            
            if name and entity_type:
                entity_key = (name, entity_type)
                # 如果实体已存在，合并属性
                if entity_key in entities_dict:
                    # 确保已存在的 attributes 是字典
                    if entities_dict[entity_key]["attributes"] is None:
                        entities_dict[entity_key]["attributes"] = {}
                    # 合并属性，新属性覆盖旧属性
                    entities_dict[entity_key]["attributes"].update(attributes)
                else:
                    entities_dict[entity_key] = {
                        "name": name,
                        "type": entity_type,
                        "attributes": attributes.copy() if attributes else {}
                    }

        """
        {
            ("当归", "Herb"):{"name":"当归", "type":"Herb", "attributes":{"meridian":"归肺经、脾经、大肠经"}}
        }
        """
        
        # 解析关系
        for relation in extract_dict.get("relations", []):
            subject = relation.get("subject")
            subject_type = relation.get("subject_type")
            relation_type = relation.get("relation")
            object_name = relation.get("object")
            object_type = relation.get("object_type")
            
            if subject and subject_type and relation_type and object_name and object_type:
                relations_list.append({
                    "subject": subject,
                    "subject_type": subject_type,
                    "relation": relation_type,
                    "object": object_name,
                    "object_type": object_type
                })
    
    return entities_dict, relations_list


def create_entity_cypher_queries(entities_dict):
    """
    为所有实体创建 Cypher MERGE 查询
    返回: List[Tuple[query, params]]
    """
    queries = []
    
    for (name, entity_type), entity_data in tqdm(entities_dict.items(), desc="生成实体查询"):
        attributes = entity_data.get("attributes") or {}
        if not isinstance(attributes, dict):
            attributes = {}
        
        # 使用 MERGE 创建节点，然后使用 SET 更新所有属性
        # 注意：属性名需要是有效的标识符，如果属性名包含特殊字符，需要处理
        query = f"MERGE (n:{entity_type} {{name: $name}}) SET n += $props"
        
        params = {
            "name": name,
            "props": attributes  # 只传递 attributes，name 已经在 MERGE 中使用
        }
        
        queries.append((query, params))
    
    return queries


def create_relation_cypher_queries(relations_list):
    """
    为所有关系创建 Cypher MERGE 查询
    返回: List[Tuple[query, params]]
    """
    queries = []
    
    for relation in tqdm(relations_list, desc="生成关系查询"):
        subject = relation["subject"]
        subject_type = relation["subject_type"]
        relation_type = relation["relation"]
        object_name = relation["object"]
        object_type = relation["object_type"]
        
        # 使用 MERGE 确保实体存在，然后创建关系
        # 使用 MERGE 创建关系，避免重复
        query = (
            f"MERGE (s:{subject_type} {{name: $subject_name}}) "
            f"MERGE (o:{object_type} {{name: $object_name}}) "
            f"MERGE (s)-[r:{relation_type}]->(o)"
        )
        
        params = {
            "subject_name": subject,
            "object_name": object_name
        }
        
        queries.append((query, params))
    
    return queries


def insert_to_neo4j(json_path, batch_size=1000):
    """
    将 JSON 数据插入到 Neo4j
    :param json_path: JSON 文件路径
    :param batch_size: 批量插入的大小
    """
    print(f"\n开始处理文件: {json_path}")
    
    # 1. 加载数据
    data = load_json_data(json_path)
    
    # 2. 解析实体和关系
    entities_dict, relations_list = parse_entities_and_relations(data)
    
    print(f"\n解析完成:")
    print(f"  - 实体数量: {len(entities_dict)}")
    print(f"  - 关系数量: {len(relations_list)}")
    
    # 3. 生成实体查询
    print("\n正在生成实体查询...")
    entity_queries = create_entity_cypher_queries(entities_dict)
    
    # 4. 生成关系查询
    print("\n正在生成关系查询...")
    relation_queries = create_relation_cypher_queries(relations_list)
    
    # 5. 批量插入实体
    print(f"\n正在插入 {len(entity_queries)} 个实体...")
    for i in tqdm(range(0, len(entity_queries), batch_size), desc="插入实体"):
        batch = entity_queries[i:i + batch_size]
        neo4j_client.run_multiple_cypher(batch)
    
    # 6. 批量插入关系
    print(f"\n正在插入 {len(relation_queries)} 个关系...")
    for i in tqdm(range(0, len(relation_queries), batch_size), desc="插入关系"):
        batch = relation_queries[i:i + batch_size]
        neo4j_client.run_multiple_cypher(batch)
    
    print(f"\n文件 {json_path} 处理完成！")


def main():
    """主函数"""
    # 文件路径
    formula_json_path = get_file_path("__002__extract_information/extract_formula_data.json")
    herb_json_path = get_file_path("__002__extract_information/extract_herb_data.json")
    
    # 先清空数据库（可选，根据需要取消注释）
    # print("正在清空数据库...")
    # neo4j_client.run_cypher("MATCH (n) DETACH DELETE n")
    
    # 插入方剂数据
    insert_to_neo4j(formula_json_path)
    
    # 插入中药数据
    insert_to_neo4j(herb_json_path)
    
    print("\n所有数据插入完成！")


if __name__ == '__main__':
    main()

