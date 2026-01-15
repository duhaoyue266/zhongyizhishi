from sentence_transformers import SentenceTransformer

from common.config import Config

conf = Config()

my_embedding_model = SentenceTransformer(conf.EMBEDDING_MODEL_PATH)