# Master thesis from Martin Böckling
## Introduction
This repository is a code collection for all aspects regarding the master thesis of Martin Böckling. The structure of the repository is structured into the CRISP-DM phases Data Understanding, Data Preparation and Data Modelling. The thesis document is provided separately. 
## Dependencies
The coding related to the thesis is implemented in Python and R. For the different programming languages the dependencies are outlined in the following sections.

### R
The R coding is based on the R version 4.1.2.
The dependencies of the project can be found in the [renv.lock](wildfirearea/renv.lock) file. The dependencies can directly be installed in R by using the [renv](https://cran.r-project.org/web/packages/renv/index.html) package. To install all necessary packages simply use the command `renv::restore(lockfile='*lockfile path*')` within your R environment.

For using the geospatial packages like sf within R GDAL, GEOS and Proj.4 needs to be installed. Instructions for downloading can be found under the following [link](https://r-spatial.github.io/sf/#installing)

### Python
The python coding is based on python version 3.9.12.
The dependencies can be found in the [requirements.txt](wildfirearea/requirements.txt) file. To install the packages used in this project please run `pip install -r requirements.txt` in your created virtual environement. 

>Example virtuelenv creation: `virtualenv wildfire -p` *path to python 3.9.12 environment*

For the igraph package you must assure that the required dependencies on a C environemnt are met. Therefore please make sure to follow the [installation guidelines provided by igraph](https://igraph.org/python/#pyinstall).
## Setup for github repo


## Data
The data can be found under the following OneDrive [Folder](https://1drv.ms/u/s!AijsqF7qjxxBiNhW7pu3QFB4LJxgPg?e=W37f3T). The structure is the same and the individual folders should be placed into the Data folder. The provided coding uses relative paths, therefore make sure to make the necessary changes to your selected editor.

## Data Mining Pipeline
The Data Mining Pipeline shows the overall procedure and steps taken for this master thesis. An outline can be found in image *discusion*

![Data Mining Pipeline](img/)

## Code Structure
In the following list the structure of the repository with the associated files are highlighted. 
- Data Understanding
  - [Data visualization script](wildfirearea/dataunderstanding/datavisualization.R) (Contains plot visualization coding that are used within the thesis document)
  - [Data Understanding script](wildfirearea/dataunderstanding/SpatialDataUnderstanding.R) (Contains visualizations related to the Data Understanding chapter of the thesis document)
- Data Preparation
  - [Data Unification](wildfirearea/datapreparation/weather/dataunification.py) (Combines single weather files into one file using pandas library)
  - [Data Preparation](wildfirearea/datapreparation/datapreparation.R) (Data Preparation script which involves weather interpolation)
  - [RDF2Vec script](wildfirearea/modelling/rdf2vec.py) (Script which transforms Knowledge Graph into vector representation)
  - [Use Case data preparation](wildfirearea/datapreparation/usecasecreation.R) (script which creates the use case datasets on which master thesis is conducted)
- Modeling
  - [XgBoost classification](wildfirearea/modelling/extragboost.py) (Script using the xgboost python package for wildfire classification)

