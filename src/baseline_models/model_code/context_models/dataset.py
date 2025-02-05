from tqdm import tqdm 
from datetime import datetime
import os
import numpy as np
from pathlib import Path

from baseline_models.utils.utils import return_logger
logger = return_logger(__name__)

class Dataset:
    def __init__(self,
                 dataset_path,
                 dest_dir,
                 shuffle=True,
                 test_ratio=0.1,
                 n_limit=-1
                 ):
        """
        Params:
        dataset_path (string): dataset file path
        dest_dir (string): destination directory path
        shuffle (bool): whether to shuffle
        test_ratio(float): proportion of test set [must be between 0-1] 
        n_limit(int): number of games to include, -1 means include all
        """

        self.dataset_path = dataset_path
        self.dest_dir = dest_dir
        self.shuffle = shuffle
        self.test_ratio = test_ratio
        self.n_limit = n_limit
        self.n_train_examples = 0
        self.n_test_examples = 0
    
    def get_max_n(self):
        """
        Get the total number of games in the dataset file
        """
        with open(self.dataset_path, "r") as dataset_file:
            max_n = 0
            for line in dataset_file:
                max_n += 1
        return max_n
    
    def gen_train_test_dest(self):
        """
        Generate directory storing train and test file. Name format of the directory is DDMMYY_HH-MM-SS
        """
        time_mark = datetime.now().strftime("%d%m%y_%H-%M-%S")
        train_test_dest = os.path.join(self.dest_dir,time_mark)
        if not os.path.isdir(train_test_dest):
            os.makedirs(train_test_dest)
        return train_test_dest
    
    def train_test_split(self):
        """
        Generate separate files (train.json, test.json) 
        that contains training examples and testing examples

        Return:
            (dict) - 
                'train_path': (str) path to generated train file 
                'test_path': (str) path to generated test file
                'n_train': (int) number of training examples in generated train file
                'n_test': (int) number of testing examples in generated test file
        """
        max_n = self.get_max_n()
        logger.info(f"Dataset '{self.dataset_path}' has {max_n} games in total")

        if (self.n_limit > max_n) or (self.n_limit < 0):
            self.n_limit = max_n
        logger.info(f"Generated dataset considers first {self.n_limit} games")

        if (self.test_ratio < 0 or self.test_ratio > 1):
            raise Exception("Test split must be in between 0 and 1")
        
        logger.info(f"Train test split is {1-self.test_ratio}/{self.test_ratio}")

        self.n_test_examples = int(self.test_ratio * self.n_limit)
        self.n_train_examples = self.n_limit - self.n_test_examples

        logger.info(f"Number of examples: {self.n_train_examples}-train, {self.n_test_examples}-test")

        train_test_dest = self.gen_train_test_dest()
        train_path = os.path.join(train_test_dest, "train.json")
        test_path = os.path.join(train_test_dest, "test.json")

        logger.info(f"Begin writing examples to: train='{train_path}', test='{test_path}'")

        idxs = np.arange(self.n_limit)
        if self.shuffle:
            np.random.shuffle(idxs)
        test_idxs = set(idxs[:self.n_test_examples])

        with open(self.dataset_path, "r") as dataset_file, open(train_path, "w") as train_set, open(test_path, "w") as test_set:
            for i, line in enumerate(tqdm(dataset_file, total=self.n_limit, desc="Generating dataset")):
                if i >= self.n_limit:
                    break
                if i in test_idxs:
                    test_set.write(line)
                else:
                    train_set.write(line)
        
        
        logger.info(f"Finished writing examples to: train='{train_path}', test='{test_path}'")

        return {"train_path": train_path, 
                "test_path": test_path,
                "n_train": self.n_train_examples,
                "n_test": self.n_test_examples
                }

if __name__ == "__main__":

    # Example usage
    data_dir = os.path.join(str(Path(__file__).resolve().parents[4]), "data")
    dataset_path = os.path.join(data_dir, "dipnet-data-diplomacy-v1-27k-msgs", "standard_no_press.jsonl")
    dataset_obj = Dataset(dataset_path=dataset_path, 
            dest_dir=data_dir,
            shuffle=True,
            test_ratio=0.1,
            n_limit=100 # limit to consider first 100 games only
            )
    
    res = dataset_obj.train_test_split()
    print(f"""GENERATED DATASET INFO:
          train data path={res["train_path"]}
          test data path={res["test_path"]}
          no. train={res["n_train"]}
          no. test={res["n_test"]}""")