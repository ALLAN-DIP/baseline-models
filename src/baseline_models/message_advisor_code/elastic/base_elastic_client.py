"""Abstract base class for elastic search client to store and search messages sent in diplomacy games as vector database."""

import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from elasticsearch import Elasticsearch
from baseline_models.model_code.constants import POWERS
from baseline_models.utils.utils import return_logger

logger = return_logger(__name__)


@dataclass
class BaseElasticClient(ABC):
    """Abstract base class for elastic search client to store and search messages sent in diplomacy games as vector database."""
    vector_element_type: str
    debug: bool = False

    @abstractmethod
    def __init__(self, host: str, username: str, password: str, cert_path: str, **kwargs):
        self.client = Elasticsearch(
            host,
            ca_certs = cert_path,
            http_auth = (username, password))

    def create_index(self, index):
        """
        Create index.
        """
        self.client.indices.delete(index=index, ignore_unavailable=True)
        self.client.indices.create(index=index, mappings={
            "properties": {
                "embedding": {
                    "type": "dense_vector",
                    "element_type": self.vector_element_type,
                },
                "messages": {
                    "type": "text",
                },
                "tags": {
                    "type": "keyword",
                }
            }
        })

    def populate_index(self, index, data_path):
        """
        Populate index.
        """
        attribute_list, message_list = self.preprocess_data(data_path)

        for atrb, msg in zip(attribute_list, message_list):
            if not msg:
                # Skip pairs with no messages
                continue

            tags = set()
            for message in msg:
                tags.add(message["sender"] + "-" + message["recipient"])

            self.client.index(index = index, document = {
                "embedding": atrb.astype(float),
                "messages": json.dumps(msg),
                "tags": list(tags),
            })


    def get_docs(self, index: str, state: dict, num_candidates: int, k: int):
        """
        Retrieve k nearest documents from index.
        """
        attribute = self.get_embedding(state)

        results = self.client.search(
            index = index,
            knn = {
                "field": "embedding",
                "query_vector": attribute,
                "num_candidates": num_candidates,
                "k": k,
            },
            size = k
        )

        docs = results["hits"]["hits"]
        return docs


    def get_docs_by_tag(self, index: str, state: dict, num_candidates: int, k: int, tag: str):
        """
        Retrieve k nearest documents from index, filtered by tag
        """
        attribute = self.get_embedding(state)

        filters = []
        filters.append({
            "term": {
                "tags": {
                    "value": tag
                }
            },
        })
        
        results = self.client.search(
            index = index,
            knn = {
                "field": "embedding",
                "query_vector": attribute,
                "num_candidates": num_candidates,
                "k": k,
                "filter": filters,
            },
            size = k,
        )

        docs = results["hits"]["hits"]
        return docs


    def get_messages_from_sender(self, index: str, state: dict, sender: str, num_candidates: int = 50, k: int = 10):
        """
        Retrieves message recommendations for a power to send to other powers given game state.
        """
        result = dict()
        for power in POWERS:
            if power == sender:
                continue
            docs = self.get_docs_by_tag(index, state, num_candidates, k, sender + "-" + power)
            for doc in docs:
                messages = json.loads(doc["_source"]["messages"])
                for message in messages:
                    if message["sender"] == sender and message["recipient"] == power:
                            
                        if not validate_message(message["message"]):
                            # skip invalid messages
                            continue

                        cleaned_message = clean_message(message["message"])
                        if self.debug:
                            cleaned_message = cleaned_message + f" [{doc['_score']:.{3}f}]"

                        if message["recipient"] not in result.keys():
                            result[message["recipient"]] = list()
                        result[message["recipient"]].append(cleaned_message)

        return result
    
    @abstractmethod
    def preprocess_data(self, data_path, **kwargs):
        """Generate embedding-message pairs from dataset.

        Returns:
            list of embeddings and list of messages
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_embedding(self, state, **kwargs):
        """Generate embedding from game state.

        Returns:
            embedding
        """
        raise NotImplementedError


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
    corrupted_newline_cnt = msg_txt.count("~N~")
    if corrupted_newline_cnt > 0:
        for i in reversed(range(1, corrupted_newline_cnt + 1)):
            # replace `i` corrupted newlines in a row
            corrupted_newlines = " " + " ".join(["~N~" for _ in range(i)]) + " "
            fixed_newlines = '\n' * i
            msg_txt = msg_txt.replace(corrupted_newlines, fixed_newlines)

    return msg_txt