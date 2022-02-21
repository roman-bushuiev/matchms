import os
import numpy as np
from matchms import Pipeline


module_root = os.path.join(os.path.dirname(__file__), "..")
spectrums_file = os.path.join(module_root, "tests", "massbank_five_spectra.msp")


def test_pipeline():
    pipeline = Pipeline()
    pipeline.query_data = spectrums_file
    pipeline.score_computations = [["precursormzmatch",  {"tolerance": 120.0}],
                                   ["modifiedcosine", {"tolerance": 10.0}]]
    pipeline.run()

    assert len(pipeline.spectrums_1) == 5
    assert pipeline.spectrums_1[0] == pipeline.spectrums_2[0]
    assert pipeline.is_symmetric is True
    assert pipeline.scores.scores.shape == (5, 5, 3)
    assert pipeline.scores.score_names == ('PrecursorMzMatch', 'ModifiedCosine_score', 'ModifiedCosine_matches')
    all_scores = pipeline.scores.to_array()
    expected = np.array([[1., 0.30384404],
                         [0.30384404, 1.]])
    assert np.allclose(all_scores["ModifiedCosine_score"][3:, 3:], expected)
    
    

