"""Elastic search client using autoencoder."""

from abc import ABC
from dataclasses import dataclass
from elasticsearch import Elasticsearch
from baseline_models.model_code.auto_encoder import get_encoding, batch_get_encoding
from baseline_models.message_advisor_code.elastic.base_elastic_client import BaseElasticClient
from baseline_models.model_code.preprocess import generate_attribute, generate_attribute_message_pair
from baseline_models.utils.utils import return_logger

logger = return_logger(__name__)


@dataclass
class AutoencoderClient(BaseElasticClient, ABC):
    """Elastic search client using autoencoder."""

    vector_element_type = "float"
    debug = False

    def __init__(self, host: str, username: str, password: str, cert_path: str, model_path: str):
        self.client = Elasticsearch(
            host,
            ca_certs = cert_path,
            http_auth = (username, password))
        self.model_path = model_path

    def preprocess_data(self, data_path):
        """Generate embedding-message pairs from dataset."""
        attribute_list = list()
        message_list = list()
        logger.info("Preprocessing data")
        with open(data_path, "r") as data:
            attribute_list, message_list = generate_attribute_message_pair(data)
            assert len(attribute_list) == len(message_list)

        attribute_list = batch_get_encoding(self.model_path, attribute_list, 500)

        return attribute_list, message_list

    def get_embedding(self, state):
        """
        Preprocess attribute to doc embedding.
        """
        attribute = generate_attribute(state)
        attribute = get_encoding(self.model_path, attribute)
        attribute = attribute.astype(float)
        return attribute