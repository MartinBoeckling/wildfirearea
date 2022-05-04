import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report

def dataPreprocess(dataPath, testDate):
    print('Data Preprocessing')
    dataPath = Path(dataPath)
    data = pd.read_csv(dataPath)
    data['DATE'] = pd.to_datetime(data['DATE'])
    trainData = data[data['DATE'] < testDate]
    testData = data[data['DATE'] >= testDate]
    trainDataY = trainData['WILDFIRE']
    trainDataX = trainData.drop(columns=['WILDFIRE', 'DATE'], axis=1)
    testDataY = testData['WILDFIRE']
    testDataX = testData.drop(columns=['WILDFIRE', 'DATE'], axis=1)
    return (trainDataX, trainDataY), (testDataX, testDataY)

def randomForest(dataTrain, dataTest):
    print('Random Forest started')
    dataTrainX = dataTrain[0]
    dataTrainY = dataTrain[1]
    dataTestX = dataTest[0]
    dataTestY = dataTest[1]

    numericTransformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median'))
    ])
    numericFeatures = dataTrainX.select_dtypes(include=['int64', 'float64']).columns
    categoricalFeatures = dataTestX.select_dtypes(include=['object']).columns
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numericTransformer, numericFeatures)])
    
    rf = Pipeline(steps=[('preprocessor', preprocessor),
                         ('classifier', RandomForestClassifier(n_estimators=1000, verbose=2, random_state=15, class_weight='balanced_subsample'))])
    rf.fit(dataTrainX, dataTrainY)
    predClass = rf.predict(dataTestX)
    print(predClass)
    print(f'Model score: {classification_report(dataTestY, predClass)}')

if __name__ =='__main__':
    trainData, testData = dataPreprocess('data/usecase/usecase1.csv', '2020-01-01')
    randomForest(trainData, testData)