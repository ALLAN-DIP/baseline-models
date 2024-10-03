from constants import *
import os
import pickle
from preprocess_v2 import key_to_filename

class Results():
    def __init__(self, model_path):
        self.model_path = model_path

        self.class_corrects = dict()
        self.class_totals = dict()
        self.class_accuracies = dict()

        self.all_correct = 0
        self.all_total = 0
        self.all_accuracy = None

    def __repr__(self):
        output = f"Complete Correct: {self.all_correct}\nComplete Total: {self.all_total}\nComplete Accuracy: {(100 * self.all_accuracy):.2f}%"
        for model_type in self.class_accuracies.keys():
            output += f"\nClass Correct ({model_type}): {(self.class_corrects[model_type])}\n"
            output += f"Class Total ({model_type}): {(self.class_totals[model_type])}\n"
            output += f"Class Accuracy ({model_type}): {(100 * self.class_accuracies[model_type]):.2f}%\n"
        return output

    def evaluate(self, test_dict):
        for model_type, data in test_dict.items():
            print(f"Predicting for key {model_type}")

            class_correct = 0
            class_total = 0
            true_orders = data[1]

            file_path = os.path.join(self.model_path, key_to_filename(model_type))
            if os.path.exists(file_path):
                pred_orders = []
                with open(file_path, 'rb') as model_file:
                    model = pickle.load(model_file)
                    pred_orders = model.predict(data[0])

                for pred, true in zip(pred_orders, true_orders):
                    if (pred == true):
                        class_correct += 1
                    class_total += 1
            else:
                print(f"Model not found | key: {model_type}")
                class_total += len(true_orders)

            self.class_corrects[model_type] = class_correct
            self.class_totals[model_type] = class_total
            self.class_accuracies[model_type] = class_correct / class_total
            self.all_correct += class_correct
            self.all_total += class_total

        self.all_accuracy = self.all_correct / self.all_total

def evaluate_model(test_dict, model_path):
    results = Results(model_path)
    results.evaluate(test_dict)
    return results