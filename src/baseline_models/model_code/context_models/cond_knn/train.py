import os
from datetime import datetime
import pickle
from tqdm.auto import tqdm

from baseline_models.utils.utils import return_logger
logger = return_logger(__name__)


from baseline_models.model_code.context_models.cond_knn.dataloader import DataLoader
from baseline_models.model_code.evaluation import evaluate_model
from baseline_models.model_code.context_models.utils import TestStats

from sklearn.neighbors import KNeighborsClassifier
from baseline_models.model_code.context_models.cond_knn.predict import predict


"""
Conditional kNN

Filters the nearest neighbours to only predict on
neighbours with orders that is a superset of the
current state's orders (aka. context orders)
"""

def train_cond_knn(train_path: str,
                   test_path: str,
                   model_dest: str,
                   n_neighs: int = 10):

    time_mark = datetime.now().strftime("%d%m%y_%H-%M-%S")
    model_path = os.path.join(model_dest, f"knn{n_neighs}_{time_mark}")

    if not os.path.isdir(model_path):
        os.makedirs(model_path)
    
    # Train regular knn
    logger.info(f"Training kNN: train_path='{train_path}'")
    train_data = DataLoader(fpath=train_path).load()

    n_keys = len(train_data.keys())
    # Below code is the same as knn_fast.py
    for key, key_data in tqdm(train_data.items(), total=n_keys, desc="Training kNN models"):
        X, y, pow_orders = key_data
        n_samples_fit = len(X)
        n_neighs = min(n_neighs, n_samples_fit)

        model = KNeighborsClassifier(n_neighbors=n_neighs, 
                                     weights='uniform', 
                                     algorithm='ball_tree', 
                                     metric="hamming")
        model.fit(X, y)
        with open(os.path.join(model_path, key), 'wb') as model_file:
                pickle.dump(model, model_file)
    
    logger.info(f"Finished training kNN: model_path='{model_path}'")

    test_data = DataLoader(fpath=test_path, is_test=True).load()

    logger.info(f"Testing regular kNN: test_path='{test_path}'")
    regular_test_res = evaluate_model(test_data, model_path)
    logger.info(regular_test_res)

    logger.info(f"Testing conditional kNN: test_path='{test_path}'")
    test_stats = TestStats()

    n_keys = len(test_data.keys())
    for key, key_data in tqdm(test_data.items(), total=n_keys, desc="Testing cond-kNN"):
        X, y_true, contexts = key_data 
        y_pred, pred_stats = predict(key=key, 
                encodings=X, 
                contexts=contexts, 
                samples_fit_data=train_data,
                model_path=model_path
                )
        key_stats = test_stats.record(key, y_pred, y_true)
        logger.info(key_stats)
        if pred_stats is not None:
            test_stats.record_cond_knn_stats(key, pred_stats)
    
    logger.info(f"""Conditional kNN | Complete testing stats
{test_stats.get_summary_stats()}""")
    return