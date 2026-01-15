from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List, Literal, Optional, Union
import os
import json
from pathlib import Path
from tqdm import tqdm

from common.llm import my_llm

# ======================
# 枚举定义
# ======================
EntityType = Literal["Symptom", "Disease", "Formula", "Herb", "Effect", "Source"]

RelationType = Literal[
    "TREATS_DISEASE",
    "ALLEVIATES_SYMPTOM",
    "HAS_EFFECT",
    "HAS_INGREDIENT",
    "HAS_SYMPTOM",
    "FROM_SOURCE"
]


# ======================
# 属性定义
# ======================
class FormulaAttributes(BaseModel):
    alias: Optional[str] = None
    effect: Optional[str] = None
    indication: Optional[str] = None
    taboo: Optional[str] = None
    usage: Optional[str] = None


class HerbAttributes(BaseModel):
    dosage: Optional[str] = None
    effect: Optional[str] = None
    indication: Optional[str] = None
    meridian: Optional[str] = None
    origin: Optional[str] = None
    place: Optional[str] = None
    processing: Optional[str] = None
    property_flavor: Optional[str] = None
    taboo: Optional[str] = None
    traits: Optional[str] = None


# ======================
# 实体与关系结构
# ======================
class Entity(BaseModel):
    name: str
    type: EntityType
    attributes: Optional[Union[FormulaAttributes, HerbAttributes]] = None


class Relation(BaseModel):
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType


class TCMKnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]


# 初始化解析器
parser = JsonOutputParser(pydantic_object=TCMKnowledgeGraph)
"""
{
    "entities":[{"name":"麻黄汤", "type":"Formula", "attributes":{"effects":"止咳化痰"}}, {...}, {...}],
    "relations":[{"subject":"麻黄汤","subject_type":"Formula", "relation":"TREATS_DISEASE", "object":"感冒发烧", "object_type":"DISEASE"}, {...}, {...}]
}
"""


def get_prompt(text: str):
    prompt = ("你是一个中医知识图谱抽取专家。请从以下文本中提取结构化知识：\n"
              "仅当文本中存在实体之间的明确关系时（如‘某方剂治疗某疾病’、‘某药材具有某功效’、‘方剂包含药材’等），才进行抽取。\n"
              "如果文本中仅描述单个实体的信息、未涉及其他实体或关系，请不要抽取，返回空结构：\n"
              "{{\"entities\": [], \"relations\": []}}\n\n"

              "【实体类型说明】\n"
              "- Symptom：症状，如咳嗽、腹痛等\n"
              "- Disease：疾病，如感冒、肺炎、肾虚等\n"
              "- Formula：方剂，如四君子汤、桂枝汤等\n"
              "- Herb：药材，如人参、黄芪、丁香等\n"
              "- Effect：功效，如补气、活血、祛湿、止痛等\n"
              "- Source：出处，如《本草纲目》《伤寒论》等\n\n"

              "【关系类型说明】\n"
              "- TREATS_DISEASE：方剂或药材治疗某种疾病\n"
              "- ALLEVIATES_SYMPTOM：方剂或药材缓解某种症状\n"
              "- HAS_EFFECT：方剂或药材具有某种功效\n"
              "- HAS_INGREDIENT：方剂包含某种药材\n"
              "- HAS_SYMPTOM：疾病包含某种症状\n"
              "- FROM_SOURCE：方剂出自某文献或出处\n\n"

              "若文本涉及方剂或药材，请补充对应的属性字段（如功效、性味、剂量等）。\n"
              "如果文本主要是讲方剂的，请不要抽取药材的属性字段。\n"
              "如果文本主要是讲药材的，请不要抽取方剂的属性字段。\n"
              "如果值为空null，则不必显示键的值。"
              "所有输出必须严格符合以下 JSON 格式：\n"
              f"{parser.get_format_instructions()}\n\n"
              f"输入文本：{text}")
    return prompt


def extract_tcm_knowledge(text: str, verbose: bool = True):
    """
    从文本中提取中医知识图谱
    
    Args:
        text: 输入文本
        verbose: 是否打印流式输出，默认True
    
    Returns:
        提取的知识图谱数据
    """
    prompt = get_prompt(text)

    # 流式输出模版
    full_content = ""
    for chunk in my_llm.stream(prompt):
        if chunk.content:
            if verbose:
                print(chunk.content, end="", flush=True)
            full_content += chunk.content
    if verbose:
        print()

    return parser.parse(full_content)


def load_existing_results(output_json_path: str):
    """
    加载已存在的json文件结果，用于断点续跑
    
    Args:
        output_json_path: json文件路径
    
    Returns:
        已处理的文件名集合和已有的结果列表
    """
    processed_files = set()
    existing_results = []

    if os.path.exists(output_json_path):
        try:
            with open(output_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "output_list" in data:
                    existing_results = data["output_list"]
                    processed_files = {item["filename"] for item in existing_results if "filename" in item}
                    print(f"发现已存在的json文件，已处理 {len(processed_files)} 个文件，将跳过这些文件")
        except Exception as e:
            print(f"读取已存在的json文件失败: {e}，将重新开始")
            existing_results = []

    return processed_files, existing_results


def save_result_to_json(output_json_path: str, output_list: List[dict]):
    """
    将结果保存到json文件
    
    Args:
        output_json_path: json文件路径
        output_list: 结果列表
    """
    output_data = {
        "output_list": output_list
    }

    # 确保输出目录存在
    output_dir = os.path.dirname(output_json_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def save_finetune_data_to_json(finetune_output_path: str, finetune_data_list: List[dict]):
    """
    将微调语料保存到Alpaca格式的json文件
    
    Args:
        finetune_output_path: 微调语料输出文件路径
        finetune_data_list: Alpaca格式的数据列表
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(finetune_output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(finetune_output_path, 'w', encoding='utf-8') as f:
        json.dump(finetune_data_list, f, ensure_ascii=False, indent=2)


def batch_extract_from_txt_files(input_dir: str, output_json_path: str, verbose: bool = False, 
                                   resume: bool = True, export_finetune_data: bool = False, 
                                   finetune_output_path: str = None):
    """
    批量处理目录下的所有txt文件，提取知识图谱数据并保存到json文件
    每处理完一个文件立即保存，支持断点续传
    
    Args:
        input_dir: 输入目录路径（包含txt文件的目录）
        output_json_path: 输出json文件路径
        verbose: 是否显示每个文件的处理详情，默认False（批量处理时建议关闭）
        resume: 是否启用断点续传，True表示跳过已处理的文件，False表示重新处理所有文件
        export_finetune_data: 是否导出微调语料（Alpaca格式），默认False
        finetune_output_path: 微调语料输出文件路径，如果为None且export_finetune_data=True，则自动生成
    """
    # 获取所有txt文件
    txt_files = list(Path(input_dir).glob("*.txt"))

    if not txt_files:
        print(f"在目录 {input_dir} 中未找到txt文件")
        return

    print(f"找到 {len(txt_files)} 个txt文件")

    # 加载已存在的结果（断点续传）
    processed_files = set()
    output_list = []
    finetune_data_list = []
    
    if resume:
        processed_files, output_list = load_existing_results(output_json_path)
        # 过滤掉已处理的文件
        txt_files = [f for f in txt_files if f.name not in processed_files]
        if len(processed_files) > 0:
            print(f"跳过已处理的 {len(processed_files)} 个文件，剩余 {len(txt_files)} 个文件待处理")
    
    # 如果启用微调数据导出，加载已存在的微调数据
    if export_finetune_data:
        if finetune_output_path is None:
            # 自动生成微调数据文件路径
            base_path = os.path.splitext(output_json_path)[0]
            finetune_output_path = f"{base_path}_finetune.json"
        
        if os.path.exists(finetune_output_path) and resume:
            try:
                with open(finetune_output_path, 'r', encoding='utf-8') as f:
                    finetune_data_list = json.load(f)
                print(f"加载已存在的微调数据 {len(finetune_data_list)} 条")
            except Exception as e:
                print(f"读取已存在的微调数据失败: {e}，将重新开始")
                finetune_data_list = []
        
        print(f"微调语料将保存到: {finetune_output_path}")

    if not txt_files:
        print("所有文件已处理完成！")
        return

    print(f"开始批量提取知识图谱数据...")

    success_count = 0
    fail_count = 0
    
    # Alpaca格式的固定instruction
    ALPACA_INSTRUCTION = "请从以下中医文档中抽取知识图谱结构，包括实体和关系。"

    # 使用tqdm显示进度
    pbar = tqdm(txt_files, desc="处理进度", unit="个")

    for txt_file in pbar:
        try:
            # 读取文件内容
            with open(txt_file, 'r', encoding='utf-8') as f:
                text_content = f.read()

            # 更新进度条描述
            filename = txt_file.name
            pbar.set_description(f"正在处理: {filename[:20]}")

            # 提取知识图谱数据
            result_dict = extract_tcm_knowledge(text_content, verbose=verbose)
            output_item = {
                "filename": filename,
                "result": result_dict
            }
            output_list.append(output_item)
            success_count += 1

            # 每处理完一个文件立即保存
            save_result_to_json(output_json_path, output_list)
            
            # 如果启用微调数据导出，同时保存Alpaca格式数据
            if export_finetune_data:
                # 处理Pydantic模型的序列化（兼容v1和v2）
                if hasattr(result_dict, 'model_dump'):
                    result_dict_for_json = result_dict.model_dump()
                elif hasattr(result_dict, 'dict'):
                    result_dict_for_json = result_dict.dict()
                else:
                    result_dict_for_json = result_dict
                
                # 将result_dict转换为JSON字符串作为output
                output_json_str = json.dumps(result_dict_for_json, ensure_ascii=False, indent=2)
                
                alpaca_item = {
                    "instruction": ALPACA_INSTRUCTION,
                    "input": text_content,
                    "output": output_json_str
                }
                finetune_data_list.append(alpaca_item)
                
                # 立即保存微调数据
                save_finetune_data_to_json(finetune_output_path, finetune_data_list)

        except Exception as e:
            fail_count += 1
            tqdm.write(f"  ✗ 处理失败: {txt_file.name} - {str(e)}")
            # 即使失败也记录错误信息
            output_item = {
                "filename": txt_file.name,
                "result": None,
                "error": str(e)
            }
            output_list.append(output_item)
            # 保存失败记录
            save_result_to_json(output_json_path, output_list)

    pbar.close()

    print("\n" + "=" * 50)
    print("批量提取完成！")
    print(f"本次成功: {success_count} 个")
    print(f"本次失败: {fail_count} 个")
    print(f"本次处理: {len(txt_files)} 个")
    if resume and len(processed_files) > 0:
        print(f"之前已处理: {len(processed_files)} 个")
    print(f"总计结果: {len(output_list)} 个")
    print(f"结果已保存到: {output_json_path}")
    if export_finetune_data:
        print(f"微调语料已保存到: {finetune_output_path} (共 {len(finetune_data_list)} 条)")
    print("=" * 50)


if __name__ == '__main__':
    ...
    #     text = """
    #     【中药名称】人中黄
    # - 中医百科
    # - 人中黄
    #     """
    #     # 单个文件测试
    #     print(extract_tcm_knowledge(text))

    # 批量处理示例（取消注释以使用）
