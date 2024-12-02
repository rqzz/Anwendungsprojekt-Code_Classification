import FeatureExtraction
import pandas as pd
from sklearn.model_selection import GroupKFold
import xgboost as xgb
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import numpy as np


features = FeatureExtraction.feature_extraction()
data = pd.DataFrame(features)

data = data.sample(frac=1).reset_index(drop=True)
data['problem'] = data['filename'].apply(lambda x: x.split("_")[1])
data['group'] = data['problem'].astype('category').cat.codes
filenames = data['filename']
group = data['group']

x = data.drop(["filename", "label", "group", "problem"], axis=1)
y = data["label"]
splits = GroupKFold(n_splits=10)

#test_indexs = list()
all_auc_roc = []
folds_test_train_groups = {}
classifiers = []
expected_values_all = []
accuracy_scores = []
precision_scores = []
recall_scores = []
f1_scores = []


for i, (train_index, test_index) in enumerate(splits.split(x, y, groups=data['group'].tolist())):
    print("Fold ", (i))
    x_train, x_test = x.iloc[train_index], x.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]

    classifier = xgb.XGBClassifier().fit(x_train, y_train)
    y_pred = classifier.predict(x_test)
    classifiers.append(classifier) 

    auc_roc = roc_auc_score(y_test, y_pred)
    all_auc_roc.append(auc_roc)
    accuracy_scores.append(accuracy_score(y_test, y_pred))
    precision_scores.append(precision_score(y_test, y_pred))
    recall_scores.append(recall_score(y_test, y_pred))
    f1_scores.append(f1_score(y_test, y_pred))

    for i, index in enumerate(test_index):
        data.at[index, 'pred_prob_ai'] = classifier.predict_proba(x_test)[i][1]
        data.at[index, 'pred_prob_human'] = classifier.predict_proba(x_test)[i][0]
        data.at[index, 'pred_label'] = y_pred[i]
        data.at[index, 'fold'] = i

avg_accuracy = np.mean([acc for acc in accuracy_scores])
avg_precision = np.mean([prec for prec in precision_scores])
avg_recall = np.mean([rec for rec in recall_scores])
avg_f1 = np.mean([f1 for f1 in f1_scores])
avg_auc_roc = np.mean([auc_roc for auc_roc in all_auc_roc])

print("AvgAcc %.3f" %(avg_accuracy), "AvgPrec %.3f" %(avg_precision), "AvgRec %.3f" %(avg_recall), "AvgF1 %.3f" %(avg_f1), "AvgAucRoc %.3f" %(avg_auc_roc))
