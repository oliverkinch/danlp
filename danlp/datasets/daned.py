import os
import pandas as pd
import json

from danlp.download import DEFAULT_CACHE_DIR, download_dataset, _unzip_process_func, DATASETS
from danlp.utils import get_kg_context_from_wikidata_qid

class DaNED:
    """

    Class for loading the DaNED dataset.
    The DaNED dataset is derived from the Dacoref dataset which is itself based on the DDT 
    (thus, divided in train, dev and test in the same way). 
    It is annotated for named entity disambiguation (also refered as named entity linking). 

    Each entry is a tuple of a sentence and the QID of an entity. 
    The label represents whether the entity corresponding to the QID is mentioned in the sentence. 
    Each QID is linked to a knowledge graph (wikidata properties) and a description (wikidata description).

    The same sentence can appear multiple times in the dataset (associated with different QIDs). 
    But only one of them should have a label "1" (which corresponds to the correct entity). 

    :param str cache_dir: the directory for storing cached models
    :param bool verbose: `True` to increase verbosity

    """
    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.dataset_name = 'daned'
        self.file_extension = DATASETS[self.dataset_name]['file_extension']
        self.dataset_dir = download_dataset(self.dataset_name, process_func=_unzip_process_func, cache_dir=cache_dir)

        # dictionary of Wikidata properties for each QID of the dataset
        with open(os.path.join(self.dataset_dir, self.dataset_name + '.props.json')) as f:
            self.properties = json.load(f)
        # dictionary of Wikidata description for each QID of the dataset
        with open(os.path.join(self.dataset_dir, self.dataset_name + '.desc.json')) as f:
            self.descriptions = json.load(f)

    def load_with_pandas(self):
        """
        Loads the DaNED dataset in dataframes with pandas. 
        
        :return: 3 dataframes -- train, dev, test
        """

        data = {}

        for part in ['train', 'dev', 'test']:
            # dataframe with 'qid', 'sentence' and 'class' columns
            data[part] = pd.read_csv(os.path.join(self.dataset_dir, self.dataset_name + '.' + part + self.file_extension), sep='\t', encoding='utf-8').dropna()
            # adding properties to the dataframe
            data[part]['kg'] = data[part]['qid'].apply(lambda x: self.properties.get(x, None))
            # adding descriptions to the dataframe
            data[part]['description'] = data[part]['qid'].apply(lambda x: self.descriptions.get(x, None))
        
        return data['train'], data['dev'], data['test']

    def get_kg_context_from_qid(self, qid: str, output_as_dictionary=False, allow_online_search=False):
        """
        Return the knowledge context and the description of an entity from its QID.

        :param str qid: a wikidata QID
        :param bool output_as_dictionary: whether the properties should be a dictionary or a string (default)
        :param bool allow_online_search: whether searching Wikidata online when qid not in database (default False)
        :return: string (or dictionary) of properties and description
        """

        properties = self.properties.get(qid, [])
        description = self.descriptions.get(qid, "")

        if qid not in self.properties and allow_online_search:
            properties, description = get_kg_context_from_wikidata_qid(qid)

        if not output_as_dictionary:
            properties = " ".join([" ".join([p if p != None else "", v if v != None else ""]) for (p,v) in properties])

        return properties, description