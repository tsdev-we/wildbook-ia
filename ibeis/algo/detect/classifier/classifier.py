#!/usr/bin/env python2.7
from __future__ import absolute_import, division, print_function
import ibeis
from os.path import isfile, join, exists
from ibeis.algo.detect.classifier.model import Classifier_Model
from os import listdir
import utool as ut
import vtool as vt
import numpy as np
import cv2
try:
    from jpcnn.core import JPCNN_Network, JPCNN_Data
except:
    print('[ibeis.algo.detect] WARNING: Could not load CNN library for some detectors (ignore for now)')
    pass

print, print_, printDBG, rrr, profile = ut.inject(
    __name__, '[classifier]')

MODEL_DOMAIN = 'https://lev.cs.rpi.edu/public/models/'

MODEL_URLS = {
    'v1' : 'classifier.v1.npy',
}


def load_classifier(source_path='classifier',
                     cache_data_filename='data.npy',
                     cache_labels_filename='labels.npy',
                     cache=True):

    cache_data_filepath = join('extracted', cache_data_filename)
    cache_labels_filepath = join('extracted', cache_labels_filename)

    if exists(cache_data_filepath) and exists(cache_labels_filepath) and cache:
        data_list = np.load(cache_data_filepath)
        label_list = np.load(cache_labels_filepath)
        return data_list, label_list

    label_filepath = join('extracted', 'labels', source_path, 'labels.csv')
    label_dict = {}
    with open(label_filepath) as labels:
        label_list = labels.read().split()
        for label in label_list:
            label_list = label.strip().split(',')
            filename = label_list[0]
            class_ = label_list[1]
            label_dict[filename] = class_

    background_path = join('extracted', 'raw', source_path)
    filename_list = [
        f for f in listdir(background_path)
        if isfile(join(background_path, f))
    ]

    assert len(label_dict.keys()) == len(filename_list)

    data_list = []
    label_list = []
    print('Loading images...')
    filename_list = filename_list
    for index, filename in enumerate(filename_list):
        if index % 1000 == 0:
            print(index)
        label = label_dict[filename]
        filepath = join(background_path, filename)
        data = cv2.imread(filepath)
        # data = cv2.resize(data, (128, 128))
        data_list.append(data)
        label_list.append(label)

    data_list = np.array(data_list, dtype=np.uint8)
    label_list = np.array(label_list)

    np.save(cache_data_filepath, data_list)
    np.save(cache_labels_filepath, label_list)

    return data_list, label_list


def train_classifier(output_path):
    print('[classifier] Loading the classifier training data')
    data_list, label_list = load_classifier()

    print('[classifier] Loading the data into a JPCNN_Data')
    data = JPCNN_Data()
    data.set_data_list(data_list)
    data.set_label_list(label_list)

    print('[classifier] Create the JPCNN_Model used for training')
    model = Classifier_Model()

    print('[classifier] Create the JPCNN_network and start training')
    net = JPCNN_Network(model, data)
    net.train(
        output_path,
        train_learning_rate=0.01,
        train_batch_size=64,
        train_max_epochs=40,
        train_mini_batch_augment=False,
    )


def load_images(cache_data_filename='test_data.npy',
                cache_labels_filename='test_labels.npy',
                cache=True):

    cache_data_filepath = join('.', cache_data_filename)
    cache_labels_filepath = join('.', cache_labels_filename)

    if exists(cache_data_filepath) and exists(cache_labels_filepath) and cache:
        data_list = np.load(cache_data_filepath)
        label_list = np.load(cache_labels_filepath)
        return data_list, label_list

    ibs = ibeis.opendb(dbdir='/media/danger/GGR/GGR-IBEIS-TEST/')
    gid_list = ibs.get_valid_gids()
    filepath_list = ibs.get_image_paths(gid_list)

    data_list = []
    label_list = []
    for index, (gid, filepath) in enumerate(zip(gid_list, filepath_list)):
        if index % 25 == 0:
            print(index)
        data = vt.imread(filepath, orient='auto')
        data = cv2.resize(data, (192, 192), interpolation=cv2.INTER_LANCZOS4)
        aid_list = ibs.get_image_aids(gid)
        species_list = ibs.get_annot_species_texts(aid_list)
        shared_set = set(species_list) & set(['zebra_grevys', 'zebra_plains'])
        label = 'positive' if len(shared_set) > 0 else 'negative'
        data_list.append(data)
        label_list.append(label)

    data_list = np.array(data_list, dtype=np.uint8)
    label_list = np.array(label_list)

    np.save(cache_data_filepath, data_list)
    np.save(cache_labels_filepath, label_list)

    return data_list, label_list


def test_classifier(output_path):
    print('[classifier] Loading the classifier training data')
    data_list, label_list = load_images()

    print('[mnist] Loading the data into a JPCNN_Data')
    data = JPCNN_Data()
    data.set_data_list(data_list)
    data.set_label_list(label_list)

    print('[classifier] Create the JPCNN_Model used for testing')
    model = Classifier_Model('model.npy')

    print('[mnist] Create the JPCNN_network and start testing')
    net = JPCNN_Network(model, data)
    test_results = net.test(output_path, best_weights=True)
    prediction_list = test_results['label_list']
    confidence_list = test_results['confidence_list']

    best_errors = np.inf
    # conf_list = [ _ / 100.0 for _ in range(0, 101) ]
    # conf_list = [ 0.81 ]  # FOR MODEL.5.NPY
    conf_list = [ 0.96 ]  # MODEL.6.NPY
    for conf in conf_list:
        failure_path = join(output_path, 'failures')
        ut.ensuredir(failure_path)
        error_list = [0, 0, 0, 0]
        zipped = zip(data_list, label_list, prediction_list, confidence_list)
        for index, (data, label, prediction, confidence) in enumerate(zipped):
            if prediction == 'negative' and confidence < conf:
                prediction = 'positive'
                confidence == 1.0 - confidence
            if label == prediction and label == 'positive':
                error_list[0] += 1
            elif label == prediction and label == 'negative':
                error_list[1] += 1
            elif label != prediction:
                if label == 'positive':
                    error_list[2] += 1
                elif label == 'negative':
                    error_list[3] += 1
                args = (confidence, index, label, prediction)
                failure_filename = 'failure_%0.05f_%06d_%s_%s.png' % args
                failure_filepath = join(failure_path, failure_filename)
                cv2.imwrite(failure_filepath, data)
        errors = error_list[2] + error_list[3]
        total = sum(error_list)
        if errors < best_errors:
            best_errors = errors
            print(error_list)
            args = (conf, errors / total, errors, total, )
            print('Error rate %0.2f: %0.03f [ %d / %d ]' % args)


def classify_gid_list(ibs, gid_list, model='v1'):
    print('[classifier] Loading the classifier training data')
    depc = ibs.depc_annot
    config = {
        'draw_annots' : False,
        'thumbsize'   : (192, 192),
    }
    thumbnail_list = depc.get('thumbnails', gid_list, 'img', config=config)
    data_list = np.array(thumbnail_list, dtype=np.uint8)

    print('[mnist] Loading the data into a JPCNN_Data')
    data = JPCNN_Data()
    data.set_data_list(data_list)

    print('[classifier] Create the JPCNN_Model used for testing')
    url = MODEL_DOMAIN + MODEL_URLS[model]
    model_path = ut.grab_file_url(url, appname='ibeis')
    model = Classifier_Model(model_path)

    print('[mnist] Create the JPCNN_network and start testing')
    net = JPCNN_Network(model, data)
    test_results = net.test('.', best_weights=True)
    prediction_list = test_results['label_list']
    confidence_list = test_results['confidence_list']

    result_list = zip(confidence_list, prediction_list)
    return result_list


if __name__ == '__main__':
    OUTPUT_PATH = '.'
    # Train network on Classifier training data
    train_classifier(OUTPUT_PATH)
    # Test network on Classifier training data
    test_classifier(OUTPUT_PATH)
