from __future__ import absolute_import, division, print_function, unicode_literals
from ibeis_cnn.ingest_ibeis import get_cnn_classifier_cameratrap_binary_training_images_pytorch
from ibeis.control import controller_inject
from os.path import join, exists
import utool as ut
from ibeis.algo.detect import wic


PYTORCH = True


# Inject utool functions
(print, rrr, profile) = ut.inject2(__name__, '[vulcanfuncs]')


# Must import class before injection
CLASS_INJECT_KEY, register_ibs_method = (
    controller_inject.make_ibs_register_decorator(__name__))


register_api = controller_inject.get_ibeis_flask_api(__name__)


@register_ibs_method
def vulcan_imageset_train_test_split(ibs, imageset_text_list=None):

    if imageset_text_list is None:
        imageset_text_list = [
            'elephant',
            'RR18_BIG_2015_09_23_R_AM',
            'TA24_TPM_L_2016-10-30-A',
            'TA24_TPM_R_2016-10-30-A',
        ]

    imageset_rowid_list = ibs.get_imageset_imgsetids_from_text(imageset_text_list)
    gids_list = ibs.get_imageset_gids(imageset_rowid_list)
    gid_list = ut.flatten(gids_list)

    config = {
        'tile_width':   256,
        'tile_height':  256,
        'tile_overlap': 64,
    }
    tiles_list = ibs.compute_tiles(gid_list=gid_list, **config)
    tile_list = ut.flatten(tiles_list)

    aids_list = ibs.get_vulcan_image_tile_aids(tile_list)
    species_list_list = list(map(ibs.get_annot_species_texts, aids_list))
    flag_list = [
        'elephant_savanna' in species_list
        for species_list in species_list_list
    ]

    pid, nid = ibs.get_imageset_imgsetids_from_text(['POSITIVE', 'NEGATIVE'])
    gid_all_list = ibs.get_valid_gids(is_tile=None)
    ibs.unrelate_images_and_imagesets(gid_all_list, [pid] * len(gid_all_list))
    ibs.unrelate_images_and_imagesets(gid_all_list, [nid] * len(gid_all_list))

    gids = [ gid for gid, flag in zip(tile_list, flag_list) if flag == 1 ]
    print(len(gids))
    ibs.set_image_imagesettext(gids, ['POSITIVE'] * len(gids))

    gids = [ gid for gid, flag in zip(tile_list, flag_list) if flag == 0 ]
    print(len(gids))
    ibs.set_image_imagesettext(gids, ['NEGATIVE'] * len(gids))

    x = list(map(len, ibs.get_imageset_gids([pid, nid])))
    num_pos, num_neg = x

    train_imgsetid = ibs.add_imagesets('TRAIN_SET')
    test_imgsetid = ibs.add_imagesets('TEST_SET')

    train_gid_list = ibs.get_imageset_gids(train_imgsetid)
    test_gid_list = ibs.get_imageset_gids(test_imgsetid)

    train_gid_set = set(train_gid_list)
    test_gid_set = set(test_gid_list)

    ancestor_gid_list = ibs.get_vulcan_image_tile_ancestor_gids(tile_list)

    tile_train_list = []
    tile_test_list = []

    for tile_id, ancestor_gid in zip(tile_list, ancestor_gid_list):
        if ancestor_gid in train_gid_set:
            tile_train_list.append(tile_id)
        elif ancestor_gid in test_gid_set:
            tile_test_list.append(tile_id)
        else:
            raise ValueError()

    ibs.set_image_imgsetids(tile_train_list, [train_imgsetid] * len(tile_train_list))
    ibs.set_image_imgsetids(tile_test_list, [test_imgsetid] * len(tile_test_list))

    return tile_list


@register_ibs_method
def vulcan_wic_train(ibs, ensembles=5):
    pid, nid = ibs.get_imageset_imgsetids_from_text(['POSITIVE', 'NEGATIVE'])

    skip_rate_neg = 1.0 - (1.0 / ensembles)

    weights_path_list = []
    for index in range(ensembles):
        pid, nid = ibs.get_imageset_imgsetids_from_text(['POSITIVE', 'NEGATIVE'])
        data_path = join(ibs.get_cachedir(), 'extracted-%d' % (index, ))
        output_path = join(ibs.get_cachedir(), 'training', 'classifier-cameratrap-%d' % (index, ))

        extracted_path = get_cnn_classifier_cameratrap_binary_training_images_pytorch(
            ibs,
            pid,
            nid,
            dest_path=data_path,
            skip_rate_neg=skip_rate_neg,
        )
        weights_path = wic.train(extracted_path, output_path)
        weights_path_list.append(weights_path)

    return weights_path_list


@register_ibs_method
def vulcan_wic_deploy(ibs, weights_path_list):
    ensemble_path = join(ibs.get_cachedir(), 'training', 'ensemble')
    ut.ensuredir(ensemble_path)

    archive_path = '%s.tar' % (ensemble_path)
    ensemble_weights_path_list = []

    for index, weights_path in enumerate(sorted(weights_path_list)):
        assert exists(weights_path)
        ensemble_weights_path = join(ensemble_path, 'classifier.%d.weights' % (index, ))
        ut.copy(weights_path, ensemble_weights_path)
        ensemble_weights_path_list.append(ensemble_weights_path)

    ut.archive_files(archive_path, ensemble_weights_path_list, overwrite=True)
    ut.copy(archive_path, '/data/public/models/classifier2.vulcan.tar')
    return archive_path


@register_ibs_method
def vulcan_wic_validate(ibs, model_tag, imageset_text_list=None):
    if imageset_text_list is None:
        imageset_text_list = [
            'elephant',
            'RR18_BIG_2015_09_23_R_AM',
            'TA24_TPM_L_2016-10-30-A',
            'TA24_TPM_R_2016-10-30-A',
        ]

    imageset_rowid_list = ibs.get_imageset_imgsetids_from_text(imageset_text_list)
    gids_list = ibs.get_imageset_gids(imageset_rowid_list)
    gid_list = ut.flatten(gids_list)

    config = {
        'tile_width':   256,
        'tile_height':  256,
        'tile_overlap': 64,
    }
    tiles_list = ibs.compute_tiles(gid_list=gid_list, **config)
    tile_list = ut.flatten(tiles_list)

    ut.embed()

    config = {
        'classifier_two_algo': 'wic',
        'classifier_two_weight_filepath': model_tag,
    }
    scores = ibs.depc_image.get_property('classifier_two', gid_list, 'score', config=config)

    return scores


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.other.vulcanfuncs
        python -m ibeis.other.vulcanfuncs --allexamples
        python -m ibeis.other.vulcanfuncs --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    ut.doctest_funcs()
