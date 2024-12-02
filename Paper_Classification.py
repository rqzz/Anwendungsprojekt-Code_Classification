import shap
import xgboost
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold
import os
from sklearn.metrics import ( accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix)
import Paper_Extraction


features_file = '../../data/features/non_gameable_features.csv'
project_dir = os.path.dirname(os.path.abspath(__file__))
training_dir = os.path.join(project_dir, "non_gameable_ownset_features.csv")
features = Paper_Extraction.extract_metrics()
#data = pd.read_csv(features)
data = pd.DataFrame(features)

# randomize data for group k-fold
data = data.sample(frac=1).reset_index(drop=True)

# convert problem to numeric groups
data['problem'] = data['filename'].apply(lambda x: x.split("_")[1])
data['group'] = data['problem'].astype('category').cat.codes

# store identifying fields besides labels: filenames, groups
filenames = data['filename']
group = data['group']

# get features and labels
X = data.drop(['filename', 'label', 'group', 'problem'], axis=1)
y = data.label

splits = GroupKFold(n_splits=10)

# get indices for test sets
test_indexs = list()

tp_all = fn_all = tn_all = fp_all = 0

shap_values_all = []
auc_roc_all_folds = []
folds_test_train_groups = {}

classifiers = []
expected_values_all = []
shap_values_dict = {}

for i, (train_index, test_index) in enumerate(splits.split(X, y, groups=data['group'].tolist())):

    test_indexs.extend(test_index)
    
    fold = i
    print("Fold ", (i))
    X_train, X_test = X.iloc[train_index], X.iloc[test_index]
    y_train, y_test = y.iloc[train_index], y.iloc[test_index]
    train_group = group.iloc[train_index] 
    test_group = group.iloc[test_index]

    folds_test_train_groups[i] = [test_group.unique(), train_group.unique()]

    clf = xgboost.XGBClassifier()
    fit = clf.fit(X_train, y_train)
    y_pred = fit.predict(X_test)

    classifiers.append(fit) 
    auc_roc = roc_auc_score(y_test, y_pred)
    auc_roc_all_folds.append(auc_roc)
    
    cm = confusion_matrix(y_test, y_pred)

    for i, index in enumerate(test_index):
        data.at[index, 'pred_prob_ai'] = fit.predict_proba(X_test)[i][1]
        data.at[index, 'pred_prob_human'] = fit.predict_proba(X_test)[i][0]
        data.at[index, 'pred_label'] = y_pred[i]
        data.at[index, 'fold'] = len(classifiers) - 1

    tn, fp, fn, tp = cm.ravel()
    tn_all += tn
    fp_all += fp
    fn_all += fn
    tp_all += tp

    # plot 

    # SHAP explanation
    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X_test)
    for shaps in shap_values:
        shap_values_all.append(shaps)

    expected_values = explainer.expected_value
    expected_values_all.append(expected_values)

    # for the waterfall plot
    for idx, shap_value in zip(test_index, shap_values):
        shap_values_dict[idx] = shap_value

# calculate average metrics
avg_auc_roc = np.mean([x for x in auc_roc_all_folds])

# print information about the data
print("Number of features: {}".format(X.shape[1]))
print("Number of samples: {}".format(X.shape[0]))

# print information about the evaluation
print(tp_all, fn_all, tn_all, fp_all)
print("tp_all:", tp_all)
print("fn_all:", fn_all)
print("tn_all:", tn_all)
print("fp_all:", fp_all)

accuracy_score = (tp_all + tn_all) / (tp_all + tn_all + fp_all + fn_all)
precision_score = tp_all / (tp_all + fp_all)
recall_score = tp_all / (tp_all + fn_all)
f1_score = 2 * (precision_score * recall_score) / (precision_score + recall_score)

print("Average Accuracy: {:.3f}".format(accuracy_score))
print("Average Precision: {:.3f}".format(precision_score))
print("Average Recall: {:.3f}".format(recall_score))
print("Average F1 Score: {:.3f}".format(f1_score))
print("Average AUC_ROC Score: {:.3f}".format(avg_auc_roc))

## SHAP

shap.summary_plot(np.array(shap_values_all), X.reindex(test_indexs), show=False, max_display=10)