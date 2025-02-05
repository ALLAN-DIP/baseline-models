import os
import pickle

from baseline_models.utils.utils import return_logger
logger = return_logger(__name__)

class PredStats:
    def __init__(self):
        self.n_processed = 0
        self.n_regular = 0
        self.n_neighbors_pre_total = 0
        self.n_neighbors_post_total = 0
    
    def record(self, n_neighs_pre_filter, n_neighs_post_filter):
        self.n_processed += 1
        self.n_neighbors_pre_total += n_neighs_pre_filter
        self.n_neighbors_post_total += n_neighs_post_filter
        if n_neighs_post_filter == 0:
            self.n_regular += 1
    
    def _avg(val, count):
        if count == 0:
            return 0
        return val/count*1.0
    
    def get_avg_neighs(self):
        return {"pre_filter": int(PredStats._avg(self.n_neighbors_pre_total, self.n_processed)),
                "post_filter": int(PredStats._avg(self.n_neighbors_post_total, self.n_processed))}

    def get_info(self, model_key=""):
        avg_neighs_info = self.get_avg_neighs()

        return f"""Prediction Stats | {model_key}
        Total no. processed encodings: {self.n_processed}
        Average no. neighbors pre filtering: {avg_neighs_info["pre_filter"]}
        Average no. neighbours post filtering: {avg_neighs_info["post_filter"]}
        No. with 0 neighbours post filtering: {self.n_regular}"""

def filter_neighs(raw_neighs_idxs, 
                  context, 
                  samples_fit_context, 
                  samples_fit_y):
    best_vote = None
    best_vote_count = 0
    filtered_votes = dict()
    n_neighs_post_filter = 0
    for i in raw_neighs_idxs:
        if not samples_fit_context[i].issuperset(context):
            continue
        n_neighs_post_filter += 1

        y_i = samples_fit_y[i]

        # record vote from X_i (i.e., y_i)
        if filtered_votes.get(y_i) is None:
            filtered_votes[y_i] = 0
        filtered_votes[y_i] += 1

        # update best vote if vote count is highest
        if filtered_votes[y_i] > best_vote_count:
            best_vote = y_i
            best_vote_count = filtered_votes[y_i]
    return best_vote, n_neighs_post_filter

def predict(key, 
            encodings: list, 
            contexts: list,
            samples_fit_data: dict,
            model_path: str,
            ):
    preds = []
    stat_recorder = PredStats()
    # load model
    model_fpath = os.path.join(model_path, key)
    if not os.path.exists(model_fpath):
        logger.info(f"Model not found | key: {key}")
        return preds, None
    
    samples_fit_y, samples_fit_context = samples_fit_data[key][1], samples_fit_data[key][2]
    
    with open(model_fpath, "rb") as model_file:
        model = pickle.load(model_file)
        pred_neighs_matrix = model.kneighbors(encodings, return_distance=False)
        # shape: (n_neighbours, n_samples) where each neigh are represented as their index

        n_encodings = len(encodings)
        for i in range(n_encodings):
            X_i = encodings[i]
            c_i = contexts[i]
            n_neighs_pre_filter = len(pred_neighs_matrix[i])
            best_vote, n_neighs_post_filter = filter_neighs(raw_neighs_idxs=pred_neighs_matrix[i], 
                                                            context=c_i, 
                                                            samples_fit_context=samples_fit_context,
                                                            samples_fit_y=samples_fit_y)
            stat_recorder.record(n_neighs_pre_filter, n_neighs_post_filter)

            if n_neighs_post_filter > 0: 
                preds.append(best_vote)
            else:
                # run regular prediction if no neighbours after filter
                preds.append(model.predict([X_i])[0])
    logger.info(stat_recorder.get_info(model_key=key))
    return preds, stat_recorder