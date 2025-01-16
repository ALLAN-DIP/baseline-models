"""Python script to generate message index from dataset"""

from time import time
import os
from baseline_models.message_advisor_code.elastic_client import ElasticClient
from baseline_models.utils.utils import return_logger

logger = return_logger(__name__)

CERT_PATH = os.path.join("D:", os.sep, "Downloads", "http_ca.crt")
ELASTIC_USERNAME = "elastic"
ELASTIC_PASSWORD = "password"
ELASTIC_HOST = "https://localhost:9200"

def main():
    data_path = os.path.join(os.sep, "Users", "nichowil", "Documents", "github", "darpa", "data", "result", "merged.jsonl")

    es = ElasticClient(ELASTIC_HOST, ELASTIC_USERNAME, ELASTIC_PASSWORD, CERT_PATH)
    es.create_index()
    es.populate_index(data_path)

if __name__ == "__main__":
    start_time = time()
    main()
    logger.info(f"Total runtime: {(time() - start_time):.2f} seconds")