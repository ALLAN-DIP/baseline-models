from tqdm.auto import tqdm
from datetime import datetime
import os
import pickle
from sklearn.linear_model import LogisticRegression

from baseline_models.model_code.context_models.lr_context.dataloader import DataLoader
from baseline_models.model_code.evaluation import evaluate_model

from baseline_models.utils.utils import return_logger
logger = return_logger(__name__)

def train_lr_context(train_path: str,
                     test_path: str,
                     model_dest: str,
                     n_games_train: int = None,
                     n_games_test: int = None
                     ):
    time_mark = datetime.now().strftime("%d%m%y_%H-%M-%S")
    model_path = os.path.join(model_dest, f"lrcontext_{time_mark}")

    if not os.path.isdir(model_path):
        os.makedirs(model_path)
    
    logger.info(f"Training LR-context: train_path='{train_path}'")
    train_data = DataLoader(fpath=train_path, n_games=n_games_train, is_test=False).load()

    n_keys = len(train_data.keys())

    for key, key_data in tqdm(train_data.items(), total=n_keys, desc="Training LR-Context models"):
        X, y = key_data
        try:
            model = LogisticRegression(random_state=0, 
                                       solver='lbfgs', 
                                       C=0.01, 
                                       max_iter=200)
            model.fit(X, y)
            with open(os.path.join(model_dest, key), 'wb') as model_file:
                pickle.dump(model, model_file)

        except Exception as e:
            logger.info(f"Failed to train model '{key}': {e}")
    
    logger.info(f"Finished training LR-Context: model_path='{model_path}'")

    test_data = DataLoader(fpath=test_path, n_games=n_games_test, is_test=True).load()
    logger.info(f"Testing LR-Context: test_path='{test_path}'")
    
    results = evaluate_model(test_data, model_path=model_path)
    logger.info(results)
