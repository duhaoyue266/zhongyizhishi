from common.neo4j_manager import neo4j_client
from common.path_utils import get_file_path

# 导出元数据
neo4j_client.export_tcm_metadata_to_json(get_file_path("__003__create_neo4j_database/tcm_metadata.json"))