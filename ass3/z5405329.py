import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from sklearn.metrics import f1_score
from scipy.stats import pearsonr
import sys

# Q1
scaler1 = MinMaxScaler()


def get_dataSetQ1(train_csv, test_csv):
    train_data = pd.read_csv(train_csv, sep='\t')
    test_data = pd.read_csv(test_csv, sep='\t')

    # deal with missing values which are numerical
    imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
    train_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']] = imputer.fit_transform(
        train_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']])
    test_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']] = imputer.transform(
        test_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']])

    # create new feature
    train_data['Houses_to_ATM_Ratio'] = train_data['Estimated_Number_of_Houses_in_1_KM_Radius'] / \
        train_data['No_of_Other_ATMs_in_1_KM_radius']
    test_data['Houses_to_ATM_Ratio'] = test_data['Estimated_Number_of_Houses_in_1_KM_Radius'] / \
        test_data['No_of_Other_ATMs_in_1_KM_radius']

    # deal with missing values which are categorical
    train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE",
                                                                                                                                                   "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].fillna(train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].mode().iloc[0])
    test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE",
                                                                                                                                                 "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].fillna(test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].mode().iloc[0])

    encode = OrdinalEncoder()
    train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = encode.fit_transform(
        train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]])
    test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = encode.transform(
        test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]])

    train_Y = train_data['revenue']
    train_X = train_data.drop(['revenue'], axis=1)

    test_Y = test_data['revenue']
    test_X = test_data.drop(['revenue'], axis=1)

    train_X = scaler1.fit_transform(train_X)
    train_Y = scaler1.fit_transform(train_Y.values.reshape(-1, 1)).ravel()

    test_X = scaler1.fit_transform(test_X)
    test_Y = scaler1.fit_transform(test_Y.values.reshape(-1, 1)).ravel()

    return train_X, train_Y, test_X, test_Y


train_X, train_Y, test_X, test_Y = get_dataSetQ1(sys.argv[1], sys.argv[2])

model_Q1 = GradientBoostingRegressor(n_estimators=150, learning_rate=0.1, max_depth=10,
                                     criterion="squared_error", min_samples_leaf=1, min_samples_split=2).fit(train_X, train_Y)

y_pred = model_Q1.predict(test_X)
y_pred = scaler1.inverse_transform(y_pred.reshape(-1, 1)).ravel()
final = pearsonr(y_pred, test_Y)
print(f"Pearsonr on test set: {final}\n")

df_pred = pd.DataFrame({'predicted_revenue': y_pred})
# save the DataFrame as a CSV file
df_pred.to_csv('z5405329.PART1.output.csv', index=False)


# Q2

def get_dataSetQ2(train_csv, test_csv):
    scaler = StandardScaler()
    encode = OrdinalEncoder()
    train_data = pd.read_csv(train_csv, sep='\t')
    test_data = pd.read_csv(test_csv, sep='\t')

    # deal with missing values which are numerical
    imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
    train_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']] = imputer.fit_transform(
        train_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']])
    test_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']] = imputer.transform(
        test_data[['Number_of_Shops_Around_ATM', 'No_of_Other_ATMs_in_1_KM_radius', 'Estimated_Number_of_Houses_in_1_KM_Radius', 'Average_Wait_Time', 'revenue']])

    train_data['Houses_to_ATM_Ratio'] = train_data['Estimated_Number_of_Houses_in_1_KM_Radius'] / \
        train_data['No_of_Other_ATMs_in_1_KM_radius']
    test_data['Houses_to_ATM_Ratio'] = test_data['Estimated_Number_of_Houses_in_1_KM_Radius'] / \
        test_data['No_of_Other_ATMs_in_1_KM_radius']

    train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", ]] = encode.fit_transform(
        train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type"]])
    test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type"]] = encode.transform(
        test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type"]])

    # deal with missing values which are categorical
    train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE",
                                                                                                                                                   "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].fillna(train_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].mode().iloc[0])
    test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]] = test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE",
                                                                                                                                                 "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].fillna(test_data[["ATM_Zone", "ATM_Placement", "ATM_TYPE", "ATM_Location_TYPE", "ATM_looks", "ATM_Attached_to", "Day_Type", "rating"]].mode().iloc[0])
    train_Y = train_data['rating']
    train_X = train_data.drop(['rating'], axis=1)

    test_Y = test_data['rating']
    test_X = test_data.drop(['rating'], axis=1)

    train_X = scaler.fit_transform(train_X)
    test_X = scaler.transform(test_X)

    return train_X, train_Y, test_X, test_Y


train_X, train_Y, test_X, test_Y = get_dataSetQ2(sys.argv[1], sys.argv[2])

model_Q2 = RandomForestClassifier(n_estimators=200)
model_Q2.fit(train_X, train_Y)
print(model_Q2.score(test_X, test_Y))

test_Y_pred = model_Q2.predict(test_X)
f1 = f1_score(test_Y, test_Y_pred, average='micro')
print(f"F1 score on test set: {f1}\n")

df_pred = pd.DataFrame({'predicted_rating': test_Y_pred})
# save the DataFrame as a CSV file
df_pred.to_csv('z5405329.PART2.output.csv', index=False)
