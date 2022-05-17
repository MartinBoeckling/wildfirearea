# import packages
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from pyrdf2vec import RDF2VecTransformer
from pyrdf2vec.embedders import Word2Vec
from pyrdf2vec.graphs import KG, Vertex
from pyrdf2vec.walkers import RandomWalker


def dataPreparation(dataPath):
    dataPath = Path(dataPath)
    # Read a CSV file containing the entities we want to classify.
    graphData = pd.read_csv(dataPath)
    graphDataList = graphData.values.tolist()
    entitiesFrom = list(set(graphData['from']))
    entitiesTo = list(set(graphData['to']))
    entities = entitiesFrom + entitiesTo
    return graphDataList, entities

def kgCreation(inputGraphList, inputEntities):
    # initialize knowledge Graph
    osmKG = KG()
    # build knowledge graph
    for row in tqdm(inputGraphList):
        subj = Vertex(row[0])
        obj = Vertex(row[1])
        pred = Vertex(row[2], predicate=True, vprev=subj, vnext=obj)
        osmKG.add_walk(subj, pred, obj)
    # build transformer
    transformer = RDF2VecTransformer(
        Word2Vec(epochs=10),
        walkers=[RandomWalker(4, 10, with_reverse=False, n_jobs=-3)],
        verbose=1
    )
    # extract embeddings
    embeddings, literals = transformer.fit_transform(osmKG, inputEntities)
    print(literals[:8])

if __name__ == '__main__':
    graphDataList, entities = dataPreparation('data/network/openstreetmapGraph.csv')
    kgCreation(graphDataList, entities)