"""Elastic search client to store and search messages sent in diplomacy games as vector database."""

import re
import json
from elasticsearch import Elasticsearch
from baseline_models.model_code.preprocess import generate_attribute, generate_attribute_message_pair
from baseline_models.model_code.constants import POWERS
from baseline_models.utils.utils import return_logger

logger = return_logger(__name__)

CORRUPTED_NEWLINE = "~N~"
INDEX_NAME = "tagged_documents"

class ElasticClient():
    def __init__(self, host: str, username: str, password: str, cert_path: str, debug: bool = False):
        self.client = Elasticsearch(
            host,
            ca_certs = cert_path,
            http_auth = (username, password))
        self.debug = debug


    def create_index(self):
        """
        Create and populate index
        """
        self.client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
        self.client.indices.create(index=INDEX_NAME, mappings={
            "properties": {
                "embedding": {
                    "type": "dense_vector",
                    "element_type": "bit",
                },
                "messages": {
                    "type": "text",
                },
                "tags": {
                    "type": "keyword",
                }
            }
        })


    def populate_index(self, data_path):
        """
        Create and populate index
        """
        attribute_list = list()
        message_list = list()
        logger.info("Preprocessing data")
        with open(data_path, "r") as data:
            attribute_list, message_list = generate_attribute_message_pair(data)
            assert len(attribute_list) == len(message_list)

        for atrb, msg in zip(attribute_list, message_list):
            if not msg:
                # Skip pairs with no messages
                continue

            tags = set()
            for message in msg:
                tags.add(message["sender"] + "-" + message["recipient"])

            self.client.index(index = INDEX_NAME, document = {
                "embedding": atrb.astype(int),
                "messages": json.dumps(msg),
                "tags": list(tags),
            })


    def get_docs(self, state: dict, num_candidates: int, k: int):
        attribute = generate_attribute(state)

        results = self.client.search(
            index = INDEX_NAME,
            knn = {
                "field": "embedding",
                "query_vector": attribute.astype(int),
                "num_candidates": num_candidates,
                "k": k,
            },
            size = k
        )

        docs = results["hits"]["hits"]
        return docs


    def get_docs_by_tag(self, state: dict, num_candidates: int, k: int, tag: str):
        attribute = generate_attribute(state)

        filters = []
        filters.append({
            "term": {
                "tags": {
                    "value": tag
                }
            },
        })
        
        results = self.client.search(
            index = INDEX_NAME,
            knn = {
                "field": "embedding",
                "query_vector": attribute.astype(int),
                "num_candidates": num_candidates,
                "k": k,
                "filter": filters,
            },
            size = k,
        )

        docs = results["hits"]["hits"]
        return docs


    def get_messages_from_sender(self, state: dict, sender: str):
        """
        Retrieves message recommendations for a power given game state
        """
        result = dict()
        for power in POWERS:
            if power == sender:
                continue
            docs = self.get_docs_by_tag(state, 50, 10, sender + "-" + power)
            for doc in docs:
                score = doc["_score"]
                score_str = f"{score:.{3}f}"
                messages = json.loads(doc["_source"]["messages"])
                for message in messages:
                    if message["sender"] == sender and message["recipient"] == power:
                            
                        if not validate_message(message["message"]):
                            # skip invalid messages
                            continue

                        cleaned_message = clean_message(message["message"])
                        if self.debug:
                            cleaned_message = cleaned_message + f" [{score_str}]"

                        if message["recipient"] not in result.keys():
                            result[message["recipient"]] = list()
                        result[message["recipient"]].append(cleaned_message)

        return result

def validate_message(msg_txt: str) -> bool:
    # filter short messages
    if len(msg_txt) <= 10:
        return False
    # filter user ids
    if re.search(r"\[\d+\]", msg_txt):
        return False
    return True


def clean_message(msg_txt: str) -> str:
    # remove corrupt newlines
    msg_txt = uncorrupt_newlines(msg_txt)
    # remove trailing carriage return
    if msg_txt.endswith('\r'):
        return msg_txt[:-1]

    return msg_txt


def uncorrupt_newlines(msg_txt: str) -> str:
    """
    Replace corrupted newlines (~N~) with newline characters.
    """
    corrupted_newline_cnt = msg_txt.count(CORRUPTED_NEWLINE)
    if corrupted_newline_cnt > 0:
        for i in reversed(range(1, corrupted_newline_cnt + 1)):
            # replace `i` corrupted newlines in a row
            corrupted_newlines = " " + " ".join([CORRUPTED_NEWLINE for _ in range(i)]) + " "
            fixed_newlines = '\n' * i
            msg_txt = msg_txt.replace(corrupted_newlines, fixed_newlines)

    return msg_txt