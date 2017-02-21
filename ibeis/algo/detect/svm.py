# -*- coding: utf-8 -*-
"""
Interface to Darknet object proposals.
"""
from __future__ import absolute_import, division, print_function
import utool as ut
from os import listdir
from os.path import join, isfile, isdir
(print, rrr, profile) = ut.inject2(__name__, '[svm]')


VERBOSE_SVM = ut.get_argflag('--verbsvm') or ut.VERBOSE


CONFIG_URL_DICT = {
    'localizer-zebra-10'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.10.zip',
    'localizer-zebra-20'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.20.zip',
    'localizer-zebra-30'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.30.zip',
    'localizer-zebra-40'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.40.zip',
    'localizer-zebra-50'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.50.zip',
    'localizer-zebra-60'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.60.zip',
    'localizer-zebra-70'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.70.zip',
    'localizer-zebra-80'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.80.zip',
    'localizer-zebra-90'  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.90.zip',
    'localizer-zebra-100' : 'https://lev.cs.rpi.edu/public/models/classifier.svm.localization.zebra.100.zip',

    'image-zebra'         : 'https://lev.cs.rpi.edu/public/models/classifier.svm.image.zebra.pkl',

    'default'             : 'https://lev.cs.rpi.edu/public/models/classifier.svm.image.zebra.pkl',
    None                  : 'https://lev.cs.rpi.edu/public/models/classifier.svm.image.zebra.pkl',
}


def classify_helper(tup, verbose=VERBOSE_SVM):
    weight_filepath_, vector_list = tup
    # Init score and class holders
    index_list = list(range(len(vector_list)))
    score_dict = { index: [] for index in index_list }
    class_dict = { index: [] for index in index_list }
    # Load models
    model = ut.load_cPkl(weight_filepath_, verbose=verbose)
    # calculate decisions and predictions
    score_list = model.decision_function(vector_list)
    class_list = model.predict(vector_list)
    zipped = zip(index_list, score_list, class_list)
    for index, score_, class_ in zipped:
        score_dict[index].append(score_)
        class_dict[index].append(class_)
    # Return scores and classes
    return score_dict, class_dict


def classify(vector_list, weight_filepath, verbose=VERBOSE_SVM, **kwargs):
    """
    Args:
        thumbail_list (list of str): the list of image thumbnails that need classifying

    Returns:
        iter
    """
    # Get correct weight if specified with shorthand
    if weight_filepath in CONFIG_URL_DICT:
        weight_url = CONFIG_URL_DICT[weight_filepath]
        if weight_url.endswith('.zip'):
            weight_filepath = ut.grab_zipped_url(weight_url, appname='ibeis')
        else:
            weight_filepath = ut.grab_file_url(weight_url, appname='ibeis',
                                               check_hash=True)

    # Get ensemble
    is_ensemble = isdir(weight_filepath)
    if is_ensemble:
        weight_filepath_list = sorted([
            join(weight_filepath, filename) for filename in listdir(weight_filepath)
            if isfile(join(weight_filepath, filename)) and '.10.pkl' not in filename
        ])
    else:
        weight_filepath_list = [weight_filepath]
    assert len(weight_filepath_list) > 0

    # Form dictionaries
    index_list = list(range(len(vector_list)))
    score_dict = { index: [] for index in index_list }
    class_dict = { index: [] for index in index_list }

    # Generate parallelized wrapper
    vectors_list = [ vector_list for i in range(len(weight_filepath_list)) ]
    args_list = zip(weight_filepath_list, vectors_list)
    classify_iter = ut.generate(classify_helper, args_list, nTasks=len(args_list))

    # Classify with SVM for each image vector
    for score_dict_, class_dict_ in classify_iter:
        for index in index_list:
            score_dict[index] += score_dict_[index]
            class_dict[index] += class_dict_[index]

    # Organize and compute mode and average for class and score
    for index in index_list:
        score_list_ = score_dict[index]
        class_list_ = class_dict[index]
        score_ = sum(score_list_) / len(score_list_)
        class_ = max(set(class_list_), key=class_list_.count)
        class_ = 'positive' if int(class_) == 1 else 'negative'
        yield score_, class_
