from __002__extract_information.__000__extract_graph_data_utils import batch_extract_from_txt_files
from common.path_utils import get_file_path

batch_extract_from_txt_files(
    input_dir=get_file_path("__001__clawler/方剂"),
    output_json_path=get_file_path("__002__extract_information/formula_knowledge_graph.json"),
    verbose=False,  # 批量处理时建议设为False，避免输出过多
    resume=True,  # 启用断点续跑，跳过已处理的文件
    export_finetune_data=True,  # 导出微调语料（Alpaca格式）
    finetune_output_path=get_file_path("__002__extract_information/formula_knowledge_graph_finetune.json")  # 微调语料输出路径
)
