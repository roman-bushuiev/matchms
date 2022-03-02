from collections import OrderedDict
import yaml
from tqdm import tqdm
import matchms.filtering as msfilters
import matchms.importing as msimport
import matchms.similarity as mssimilarity
from matchms import calculate_scores


_importing_functions = {"json": msimport.load_from_json,
                        "mgf": msimport.load_from_mgf,
                        "msp": msimport.load_from_msp,
                        "mzml": msimport.load_from_mzml,
                        "mzxml": msimport.load_from_mzxml}
_filter_functions = {key: f for key, f in msfilters.__dict__.items() if callable(f)}
_score_functions = {key.lower(): f for key, f in mssimilarity.__dict__.items() if callable(f)}


class Pipeline:
    """Central pipeline class.

    """
    def __init__(self, config_file=None, progress_bar=True):
        """
        """
        self.spectrums_queries = []
        self.spectrums_references = []
        self.is_symmetric = False
        self._initialize_workflow_dict(config_file)
        self.scores = None
        self.progress_bar = progress_bar

    def _initialize_workflow_dict(self, config_file):
        if config_file is None:
            self.workflow = OrderedDict()
            self.workflow["importing"] = {"queries": None,
                                          "references": None}
            self.workflow["filtering_queries"] = ["defaults"]
            self.workflow["filtering_refs"] = ["defaults"]
            self.workflow["score_computations"] = []
        else:
            with open(config_file, 'r', encoding="utf-8") as file:
                self.workflow = ordered_load(file, yaml.SafeLoader)
            if self.workflow["filtering_refs"] == "filtering_queries":
                self.workflow["filtering_refs"] = self.workflow["filtering_queries"]

    def import_workflow_from_yaml(self, config_file):
        self._initialize_workflow_dict(config_file)

    def run(self):
        self.check_pipeline()
        self.import_data(self.query_files,
                         self.reference_files)

        # Processing
        for spectrum in tqdm(self.spectrums_queries,
                             disable=(not self.progress_bar),
                             desc="Processing query spectrums"):
            for step in self.filter_steps_queries:
                if step[0] in _filter_functions:
                    self.apply_filter(spectrum, step)
        if self.is_symmetric is False:
            for spectrum in tqdm(self.spectrums_references,
                                 disable=(not self.progress_bar),
                                 desc="Processing reference spectrums"):
                for step in self.filter_steps_refs:
                    if step[0] in _filter_functions:
                        self.apply_filter(spectrum, step)
        # Score computation and masking
        for i, computation in enumerate(self.score_computations):
            if i == 0:
                similarity_function = _score_functions[computation[0]](**computation[1])
                self.scores = calculate_scores(self.spectrums_queries,
                                               self.spectrums_references,
                                               similarity_function,
                                               is_symmetric=self.is_symmetric)
            else:
                similarity_func = _score_functions[computation[0]](**computation[1])
                new_scores = similarity_func.sparse_array(references=self.spectrums_queries,
                                                          queries=self.spectrums_references,
                                                          idx_row=self.scores.scores.row,
                                                          idx_col=self.scores.scores.col,
                                                          is_symmetric=self.is_symmetric)
                self.scores.scores.add_sparse_data(new_scores, similarity_func.__class__.__name__)

    def check_pipeline(self):
        # check if files exist
        # check if all steps exist
        pass

    def import_data(self, query_files, reference_files=None):
        if isinstance(query_files, str):
            query_files = [query_files]
        if isinstance(reference_files, str):
            reference_files = [reference_files]
        spectrums_queries = []
        for query_file in query_files:
            spectrums_queries += _spectrum_importer(query_file)
        self.spectrums_queries += spectrums_queries
        if reference_files is None:
            self.is_symmetric = True
            self.spectrums_references = self.spectrums_queries
        else:
            spectrums_references = []
            for reference_file in reference_files:
                spectrums_references += _spectrum_importer(reference_file)
            self.spectrums_references += spectrums_references

    def apply_filter(self, spectrum, filter_step):
        filter_name = filter_step[0]
        if len(filter_step) > 1:
            filter_params = filter_step[1]
            spectrum = _filter_functions[filter_name](spectrum, **filter_params)
        else:
            spectrum = _filter_functions[filter_name](spectrum)

    def create_workflow_config_file(self, filename):                   
        with open(filename, 'w', encoding="utf-8") as file:
            file.write("# Matchms pipeline config file \n")
            file.write("# Change and adapt fields where necessary \n")
            file.write("# " + 20 * "=" + " \n")
            ordered_dump(self.workflow, file)

    # Getter & Setters
    @property
    def query_files(self):
        return self.workflow["importing"].get("queries")

    @query_files.setter
    def query_files(self, filter_list):
        self.workflow["importing"]["queries"] = filter_list

    @property
    def reference_files(self):
        return self.workflow["importing"].get("references")

    @reference_files.setter
    def reference_files(self, files):
        self.workflow["importing"]["references"] = files

    @property
    def filter_steps_queries(self):
        return self.workflow.get("filtering_queries")

    @filter_steps_queries.setter
    def filter_steps_queries(self, files):
        self.workflow.set("filtering_queries", files)

    @property
    def filter_steps_refs(self):
        return self.workflow.get("filtering_refs")

    @filter_steps_refs.setter
    def filter_steps_refs(self, filter_list):
        self.workflow["filtering_refs"] = filter_list

    @property
    def score_computations(self):
        return self.workflow.get("score_computations")

    @score_computations.setter
    def score_computations(self, computations_list):
        self.workflow["score_computations"] = computations_list


def _spectrum_importer(filename):
    file_ending = filename.split(".")[-1]
    importer_function = _importing_functions.get(file_ending)
    return list(importer_function(filename))


def ordered_load(stream, loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
    """ Code from https://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    """
    class OrderedLoader(loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def ordered_dump(data, stream=None, dumper=yaml.SafeDumper, **kwds):
    class OrderedDumper(dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)
