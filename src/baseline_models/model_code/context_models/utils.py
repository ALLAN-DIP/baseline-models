import numpy as np
import baseline_models.model_code.context_models.cond_knn.predict as cond_knn_predict

def gen_one_hot(size: int, non_zero_idx: int):
    """
    Returns a 1-dimensional one hot encoded numpy array

    Params:
        size (int): size of the numpy array
        non_zero_idx (int): the non zero index of the array
    """
    _vec = np.zeros([size], dtype=bool)
    if non_zero_idx is not None:
        _vec[non_zero_idx] = True
    return _vec

def gen_test_context(target, pow_orders):
    context = [o for o in pow_orders if o != target]
    pool_size = len(context)

    if pool_size == 0:
        return context
    
    # get random sample size
    sample_size = np.random.randint(pool_size)

    # shuffle to generate sampled context 
    np.random.shuffle(context)
    return context[:sample_size]

def get_avg(n_target, n_total, is_percentage=False):
    if n_total == 0:
        return 0
    if is_percentage:
        return n_target/n_total*100.0
    else:
        return n_target/n_total*1.0



class TestStats:
    shared_numeric_params = tuple(
        ["n_correct",
        "n_total",
        "accuracy"]
    )

    cond_knn_numeric_params = tuple(["n_processed", 
                                    "n_regular", 
                                    "n_neighbors_pre_total", 
                                    "n_neighbors_post_total"])

    def __init__(self):
        self.keys_stats = dict()
        for p in TestStats.shared_numeric_params:
            setattr(self, p, 0)
        
        for p in TestStats.cond_knn_numeric_params:
            setattr(self, p, None)
        
        self.recorded_cond_knn = False
    
    def y_pred_vs_y_true(y_pred, y_true):
        n_correct = 0
        n_total = len(y_true)
        if len(y_pred) != n_total:
            return n_correct, n_total, 0
        for i in range(n_total):
            if y_pred[i] == y_true[i]:
                n_correct += 1
        accuracy = get_avg(n_correct, n_total, is_percentage=True)
        return n_correct, n_total, accuracy

    def record(self, key, y_pred, y_true):
        if self.keys_stats.get(key) is None:
            self.keys_stats[key] = dict()
        n_correct, n_total, accuracy = TestStats.y_pred_vs_y_true(y_pred, y_true)

        # update key stats
        self.keys_stats[key]["n_correct"] = n_correct
        self.keys_stats[key]["n_total"] = n_total
        self.keys_stats[key]["accuracy"] = accuracy

        # update complete stats
        self.n_correct += n_correct
        self.n_total += n_total
        self.accuracy = get_avg(self.n_correct, self.n_total, is_percentage=True)

        return f""" Testing stats | {key}:
        accuracy={accuracy:.2f}%
        n_correct={n_correct}
        n_total={n_total}
        """
    
    def record_cond_knn_stats(self, key, pred_stats: cond_knn_predict.PredStats):
        self.recorded_cond_knn = True
        if self.keys_stats.get(key) is None:
            self.keys_stats[key] = dict()
        
        for p in TestStats.cond_knn_numeric_params:
            p_val = getattr(pred_stats, p, None)
            if p_val is None:
                continue

            self.keys_stats[key][p] = p_val

            # update complete stats
            prev_attr = getattr(self, p, None)
            if prev_attr is None:
                prev_attr = 0 

            setattr(self, p, prev_attr + self.keys_stats[key][p])
        return
    
    def get_summary_stats(self):
        stats_str = []
        for i in TestStats.shared_numeric_params:
            if i in ["accuracy"]:
                stats_str.append(f"{i}: {getattr(self, i):.2f}%")
            else:
                stats_str.append(f"{i}: {getattr(self, i)}")
        
        if self.recorded_cond_knn == True:
            for i in TestStats.cond_knn_numeric_params:
                stats_str.append(f"{i}: {getattr(self, i)}")
            
            stats_str.append(f"avg_n_neighs_pre_filter: {int(get_avg(self.n_neighbors_pre_total, self.n_processed))}")
            stats_str.append(f"avg_n_neighs_post_filter: {int(get_avg(self.n_neighbors_post_total, self.n_processed))}")
            stats_str.append(f"%_regular_processed: {get_avg(self.n_regular, self.n_processed, is_percentage=True):.2f}%")

        return "\n".join(stats_str)

        





