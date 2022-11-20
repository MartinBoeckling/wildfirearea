''''
Title:
Extra Gradient Boosting Script

Description:
This script uses the extra gradient boosting algorithm to predict wildfires. The
hyperparameters are optimized using bayes search cross validation implemented by 
the scikit-learn optimization package. The optimization is performed on a f1-score.
The datasets are highly imbalanced, therefore a random oversampling for the minority
class is performed. The random over sampling is implemented by the imblearn package.

Input:
    - dataPath: Path of dataset for use case in format dir/.../file
    - testDate: Date where split is performed

Output:
    - Optimal parameter combination
    - Score development over time
    - Classification report implemented by scikit-learn

'''
# import packages
import argparse
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import shap
import xgboost as xgb
from bayes_opt import BayesianOptimization
from bayes_opt.logger import JSONLogger
from bayes_opt.event import Events
from bayes_opt.util import load_logs
from imblearn.over_sampling import RandomOverSampler
import json
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder


class modelPrediction:
    def __init__(self, validation, dataPath, testDate, resume):
        # transform datafile path into pathlib object
        self.dataPath = Path(dataPath)
        # create directory for use case
        self.loggingPath = Path('wildfirearea/modeling').joinpath(self.dataPath.stem)
        self.loggingPath.mkdir(exist_ok=True, parents=True)
        self.resume = resume
        # check if input is eligeble for data processing
        # check if dataPath input is a file
        assert self.dataPath.is_file(), f'{self.dataPath} does not link to a file'
        # check if testDate input can be interpreted as date
        assert not pd.isna(pd.to_datetime(testDate, errors='coerce')), f'{testDate} is not an eligible date'
        # assign test date as class variable
        self.testDate = testDate
        # perform data preprocessing for training and test data
        trainData, testData = self.dataPreprocess()
        # perform validation if set to true
        if validation:
            parameterSettings = self.parameterTuning(trainData, testData)
        # if validation set to false empty dict is used
        else:
            parameterSettings = {'colsample_bylevel': 0.5188039103349633, 'colsample_bytree': 0.7754334015585038, 'gamma': 0.43521384299197863, 'learning_rate': 0.01796647904451973, 'max_delta_step': 6.1947185101040825, 'max_depth': int(47.92258322892866), 'min_child_weight': 5.131167122678871, 'n_estimators': int(161.3995487052345), 'reg_alpha': 0.5391999378864482, 'reg_lambda': 221.25494242853864, 'scale_pos_weight': 1612.9627160420587, 'subsample': 0.3488320793585375}
        # perform training based on train and test dataset and parametersettings
        self.modelTraining(trainData, testData, parameterSettings)
        #self.modelExplanation()

    
    def dataPreprocess(self):
        print('Data Preprocessing')
        # read file into dataframe
        data = pd.read_csv(self.dataPath)
        print(data.columns)
        # transform DATE column into datetime
        data['DATE'] = pd.to_datetime(data['DATE'])
        # check if column osmCluster is present in dataframe
        if 'osmCluster' in data.columns:
            # change datatype of column osmCluster to categorical data type
            data = data.astype({'osmCluster':'object'})
        print(pd.unique(data['WILDFIRE']))
        '''labelEncoder = LabelEncoder()
        labelEncoder.fit(data['WILDFIRE'])
        print(f'Classes: {labelEncoder.classes_} \nEncoded Values: {labelEncoder.transform(labelEncoder.classes_)}')
        data['WILDFIRE'] = labelEncoder.transform(data['WILDFIRE'])
        # extract landcover categories
        if 'LANDCOVER' in data.columns:
            landcoverCategories = pd.unique(data['LANDCOVER'])
        else:
            landcoverCategories = []
        print(landcoverCategories)'''
        # split data into train and testset based on specified date
        # create train dataframe which is under specified date
        trainData = data[data['DATE'] < self.testDate]
        # create test dataframe which is over specified date
        testData = data[data['DATE'] >= self.testDate]
        # extract wildfire column as target
        trainDataY = trainData.pop('WILDFIRE')
        # Drop geometry and ID column
        trainDataX = trainData.drop(columns=['ID', 'geometry'], axis=1, errors='ignore')
        trainDataX['DATE'] = trainDataX['DATE'].astype(object)
        roseSampling = RandomOverSampler(random_state=15)
        # resample data with specified strategy
        trainDataX, trainDataY = roseSampling.fit_resample(trainDataX, trainDataY)
        print('Finished ROSE sampling')
        trainDataY = pd.DataFrame(trainDataY, columns=['WILDFIRE'])
        trainData = pd.concat([trainDataX, trainDataY], axis=1)
        trainData['DATE'] = pd.to_datetime(trainData['DATE'])
        trainData = trainData.sort_values(by='DATE')
        # Drop Date and ID column
        trainDataY = trainData.pop('WILDFIRE')
        trainDataX = trainData.drop(columns=['DATE'], axis=1, errors='ignore')
        # extract Wildfire column as testdata target
        testDataY = testData.pop('WILDFIRE')
        # Drop Date and ID column
        testDataX = testData.drop(columns=['DATE', 'ID', 'geometry'], axis=1, errors='ignore')
        self.testData = testDataX
        # create preprocessing pipeline for numerical and categorical data
        # create numerical transformer pipeline
        numericTransformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median'))
        ])
        # create categorical transformer pipeline
        categoricTransformer = Pipeline(steps=[
            ('encoder', OneHotEncoder())
        ])
        # select columns with numerical dtypes
        numericFeatures = trainDataX.select_dtypes(include=['int64', 'float64']).columns
        # select columns with categorical dtype
        categoricFeatures = trainDataX.select_dtypes(include=['object']).columns
        # construct column transformer object to apply pipelines to each column
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numericTransformer, numericFeatures),
                ('cat', categoricTransformer, categoricFeatures)],
            n_jobs=-1, verbose=True, remainder='passthrough')
        # apply column transformer to train and test data
        trainDataX = preprocessor.fit_transform(trainDataX)
        testDataX = preprocessor.fit_transform(testDataX)
        # return trainData and testdata X and Y dataframe in tuple format
        return (trainDataX, trainDataY), (testDataX, testDataY)


    def parameterRoutineCV(self, learningRate, minChildWeight, maxDepth, maxDeltaStep,
                        subsample, colsampleBytree, colsampleBylevel, regLambda, regAlpha,
                        gamma, numberEstimators, scalePosWeight):
        
        xgbCl = xgb.XGBClassifier(objective="binary:logistic", seed=15, n_jobs=-1,
                                 learning_rate=learningRate,
                                 min_child_weight=minChildWeight,
                                 max_depth = int(maxDepth),
                                 max_delta_step = maxDeltaStep,
                                 subsample=subsample,
                                 colsample_bytree = colsampleBytree,
                                 colsample_bylevel= colsampleBylevel,
                                 reg_lambda = regLambda,
                                 reg_alpha = regAlpha,
                                 gamma = gamma,
                                 n_estimators = int(numberEstimators),
                                 scale_pos_weight = scalePosWeight)
        # create time series cross validation object
        timeSeriesCV = TimeSeriesSplit(n_splits=5)
        # calculate cross validation score
        cv = cross_val_score(estimator=xgbCl, X=self.dataTrainX, y=self.dataTrainY, scoring='f1_macro', cv=timeSeriesCV)
        return cv.mean()        

    def parameterTuning(self, dataTrain, dataTest):
        print('Parameter tuning')
        # extract dataframes from train and test data tuples
        self.dataTrainX = dataTrain[0]
        self.dataTrainY = dataTrain[1]
        dataTestX = dataTest[0]
        dataTestY = dataTest[1]
        '''
        specify bayesian search cross validation with the following specifications
            - estimator: specified extra gradient boosting classifier
            - search_spaces: defined optimization area for hyperparameter tuning
            - cv: Specifying split for cross validation with 5 splits
            - scoring: optimization function based on f1_marco-score optimization
            - verbose: Output while optimizing
            - n_jobs: Parallel jobs to be used for optimization using 2 jobs
            - n_iter: Iteration for optimization
            - refit: Set to false as only parameter settings need to be extracted
        '''
        optimizer = BayesianOptimization(f=self.parameterRoutineCV,
                                        pbounds={
                                            'learningRate': (0.01, 1.0),
                                            'minChildWeight': (0, 10),
                                            'maxDepth': (1, 50),
                                            'maxDeltaStep': (0, 20),
                                            'subsample': (0.01, 1.0),
                                            'colsampleBytree': (0.01, 1.0),
                                            'colsampleBylevel': (0.01, 1.0),
                                            'regLambda': (1e-9, 1000),
                                            'regAlpha': (1e-9, 1.0),
                                            'gamma': (1e-9, 0.5),
                                            'numberEstimators': (50, 400),
                                            'scalePosWeight': (1e-6, 2000)
                                        },
                                        verbose=2,
                                        random_state=14)
        if self.resume:
            load_logs(optimizer, logs=[f'{self.loggingPath}/logs.json'])
            with open(f'{self.loggingPath}/logs.json') as loggingFile:
                loggingFiles = [json.loads(jsonObj) for jsonObj in loggingFile]
            iterationSteps = 30 - len(loggingFiles) - 5
            initPoints = 0
        else:
            iterationSteps = 30
            initPoints = 5
        logger = JSONLogger(path=f"{self.loggingPath}/logs.json")
        optimizer.subscribe(Events.OPTIMIZATION_STEP, logger)
        optimizer.maximize(n_iter=iterationSteps, init_points=initPoints)
        print(f'Best parameter & score: {optimizer.max}')
        dataIterationPerformance = pd.json_normalize(optimizer.res)
        dataIterationPerformance.to_csv(f'{self.loggingPath}/runPerformance.csv', index=False)
        parameterNames = ['colsample_bylevel', 'colsample_bytree', 'gamma', 'learning_rate', 'max_delta_step', 'max_depth', 'min_child_weight', 'n_estimators', 'reg_alpha', 'reg_lambda', 'scale_pos_weight', 'subsample']
        parameterCombination = dict(zip(parameterNames, optimizer.max['params']))
        parameterCombination['max_depth'] = int(parameterCombination['max_depth'])
        parameterCombination['n_estimators'] = int(parameterCombination['n_estiamtors'])
        return parameterCombination
        # predict class
        """predClass = cv.predict(dataTestX)
        # print best parameter combination
        print(f'Best parameters: {cv.best_params_}')
        # store best parameter combination in pickle format
        with open(f'{self.loggingPath}/xgboostBestParams.pkl', 'wb') as f:
            pickle.dump(cv.best_params_, f)
        # print detailed results of cross validation
        print(f'Overall results: {cv.cv_results_}')
        # store results of cross validation
        with open(f'{self.loggingPath}/xgboostResults.pkl', 'wb') as f:
            pickle.dump(cv.cv_results_, f)
        # print sum of predicted classes to see number of predicted wildfires
        print(f'Sum of prediction:{sum(predClass)}' )
        # print classification report
        print(f'Model score:\n{classification_report(dataTestY, predClass)}')
        # print confusion matrix of classification
        print(f'Confusion matrix:\n{confusion_matrix(dataTestY, predClass)}')
        _ = plot_convergence(cv)
        plt.show()
        return {}"""

    def modelTraining(self, trainData, testData, parameterSettings):
        print('Model training')
        # extract dataframes from train and test data tuples
        dataTrainX = trainData[0]
        dataTrainY = trainData[1]
        dataTestX = testData[0]
        dataTestY = testData[1]
        # specify extra gradient boosting classifier
        xgbCl = xgb.XGBClassifier(**parameterSettings, objective="binary:logistic", seed=15, n_jobs=-1)
        # fit specified model to training data
        xgbCl.fit(dataTrainX, dataTrainY)
        # store model
        xgbCl.save_model(f'{str(self.loggingPath)}/trainedModel.json')
        self.model = xgbCl
        # perform prediction on test dataset with trained model
        predClass = xgbCl.predict(dataTestX)
        # calculate probability for AUC calculation
        predProb = xgbCl.predict_proba(dataTestX)[:,1]
        # print feature importance
        predProbDf = pd.DataFrame({'probability': predProb, 'actualClass': dataTestY})
        predProbDf.to_csv(f'{self.loggingPath}/probabilityClass.csv', index=False)
        print(f'Feature imporance:{xgbCl.feature_importances_}')
        # print confusion matrix of classification
        print(f'Confusion matrix:\n{confusion_matrix(dataTestY, predClass)}')
        # print AUC metric
        aucScore = roc_auc_score(dataTestY, predProb, multi_class='ovo')
        print(f'AUC Score:\n{aucScore}')
        # print classification report
        print(f'Model score:\n{classification_report(dataTestY, predClass)}')
        # save roc_curve
        # extract false positive and true positive value series
        fp, tp, _ = roc_curve(dataTestY,  predProb)
        # construct roc curve plot
        # initialize matplotlib figure
        plt.figure()
        # add roc curve to matplotlib figure
        plt.plot(fp, tp, label=f"ROC Curve (AUC={aucScore})", color='dimgray', lw=2)
        # add line regarding random performance
        plt.plot([0, 1], [0, 1], color="darkgrey", lw=2, label=f"Random guess", linestyle="--")
        # add limitations to x- and y-axis
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        # add labels to x-axis and y-axis
        plt.ylabel('True Positive Rate')
        plt.xlabel('False Positive Rate')
        plt.legend(loc="lower right")
        # save roc-curve plot
        plt.savefig(f'{str(self.loggingPath)}/rocCurve.png')
        plt.close()

    def modelExplanation(self):
        explainer = shap.TreeExplainer(self.model)
        shapValues = explainer.shap_values(self.testData)
        shap.summary_plot(shapValues, self.testData, plot_type="violin", max_display=15, show=False)
        plt.savefig(f"summaryPlotModelPerformance{self.dataPath.stem}.png", dpi=250, bbox_inches='tight')


if __name__ == '__main__':
    # initialize the command line argparser
    parser = argparse.ArgumentParser(description='XGBoost argument parameters')
    # add validation argument parser
    parser.add_argument('-v', '--validation', default=False, action='store_true',
    help="use parameter if grid parameter search should be performed")
    parser.add_argument('-r', '--resume', default=False, action='store_true',
    help="use parameter if grid parameter search should be resumed")
    # add path argument parser
    parser.add_argument('-p', '--path', type=str, required=True,
    help='string value to data path')
    # add date argument parser
    parser.add_argument('-d', '--date', type=str, required=True,
    help='date value for train test split', default='2020-01-01')
    # store parser arguments in args variable
    args = parser.parse_args()
    # Pass arguments to class function to perform xgboosting
    model = modelPrediction(validation=args.validation, dataPath=args.path, testDate=args.date, resume=args.resume)
