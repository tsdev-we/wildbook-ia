from __future__ import absolute_import, division, print_function
# Python
#from os.path import exists, join, split  # UNUSED
from os.path import splitext, exists
# UTool
from itertools import izip, imap
import utool
from vtool import image as gtool
from ibeis.model.detect import grabmodels
import pyrf
(print, print_, printDBG, rrr, profile) = utool.inject(
    __name__, '[randomforest]', DEBUG=False)


#=================
# IBEIS INTERFACE
#=================


def generate_detections(ibs, gid_list, species, **detectkw):
    """ detectkw can be: save_detection_images, save_scales, draw_supressed,
        detection_width, detection_height, percentage_left, percentage_top,
        nms_margin_percentage

        Yeilds tuples of image ids and bounding boxes
    """
    #
    # Resize to a standard image size prior to detection
    src_gpath_list = list(imap(str, ibs.get_image_detectpaths(gid_list)))

    # Get sizes of the original and resized images for final scale correction
    neww_list = [gtool.open_image_size(gpath)[0] for gpath in src_gpath_list]
    oldw_list = [oldw for (oldw, oldh) in ibs.get_image_sizes(gid_list)]
    scale_list = [oldw / neww for oldw, neww in izip(oldw_list, neww_list)]

    # Detect on scaled images
    generator = detect_species_bboxes(src_gpath_list, species, **detectkw)

    for gid, scale, (bboxes, confidences, img_conf) in izip(gid_list, scale_list, generator):
        # Unscale results
        unscaled_bboxes = [_scale_bbox(bbox_, scale) for bbox_ in bboxes]
        for index in xrange(len(unscaled_bboxes)):
            bbox = unscaled_bboxes[index]
            confidence = float(confidences[index])
            yield gid, bbox, confidence, img_conf


def get_image_hough_gpaths(ibs, gid_list, species, quick=True):
    detectkw = {
        'quick': quick,
        'save_detection_images': True,
        'save_scales': True,
    }
    #
    # Resize to a standard image size prior to detection
    src_gpath_list = list(imap(str, ibs.get_image_detectpaths(gid_list)))
    dst_gpath_list = [splitext(gpath)[0] for gpath in src_gpath_list]
    hough_gpath_list = [gpath + '_hough.png' for gpath in dst_gpath_list]
    isvalid_list = [exists(gpath) for gpath in hough_gpath_list]

    # Need to recompute hough images for these gids
    dirty_gids = utool.get_dirty_items(gid_list, isvalid_list)
    num_dirty = len(dirty_gids)
    if num_dirty > 0:
        print('[detect.rf] making hough images for %d images' % num_dirty)
        detect_gen = generate_detections(ibs, dirty_gids, species, **detectkw)
        # Execute generator
        for tup in detect_gen:
            pass

    return hough_gpath_list


#=================
# HELPER FUNCTIONS
#=================


def _scale_bbox(bbox, s):
    bbox_scaled = (s * _ for _ in bbox)
    bbox_round = imap(round, bbox_scaled)
    bbox_int   = imap(int,   bbox_round)
    bbox2      = tuple(bbox_int)
    return bbox2


def _get_detector(species, quick=True):
    # Ensure all models downloaded and accounted for
    grabmodels.ensure_models()
    # Create detector
    if quick:
        config = {}
    else:
        config = {
            'scales': '11 2.0 1.75 1.5 1.33 1.15 1.0 0.75 0.55 0.40 0.30 0.20'
        }
    detector = pyrf.Random_Forest_Detector(rebuild=False, **config)
    trees_path = grabmodels.get_species_trees_paths(species)
    # Load forest, so we don't have to reload every time
    forest = detector.load(trees_path, species + '-')
    return detector, forest


def _get_detect_config(**detectkw):
    detect_config = {
        'percentage_top':    0.40,
    }
    detect_config.update(detectkw)
    return detect_config


#=================
# PYRF INTERFACE
#=================


def detect_species_bboxes(src_gpath_list, species, quick=True, **detectkw):
    """
    Generates bounding boxes for each source image
    For each image yeilds a list of bounding boxes
    """
    nImgs = len(src_gpath_list)
    print('[detect.rf] Begining %s detection' % (species,))
    detect_lbl = 'detect %s ' % species
    mark_prog, end_prog = utool.progress_func(nImgs, detect_lbl, flush_after=1)

    detect_config = _get_detect_config(**detectkw)
    detector, forest = _get_detector(species, quick=quick)

    dst_gpath_list = [splitext(gpath)[0] for gpath in src_gpath_list]
    pathtup_iter = izip(src_gpath_list, dst_gpath_list)
    for ix, (src_gpath, dst_gpath) in enumerate(pathtup_iter):
        mark_prog(ix)
        results, timing = detector.detect(forest, src_gpath, dst_gpath,
                                          **detect_config)
        # Unpack unsupressed bounding boxes
        bboxes = [(minx, miny, (maxx - minx), (maxy - miny))
                  for (centx, centy, minx, miny, maxx, maxy, confidence, supressed)
                  in results if supressed == 0]

        confidences = [confidence
                       for (centx, centy, minx, miny, maxx, maxy, confidence, supressed)
                       in results if supressed == 0]

        if len(results) > 0:
            image_confidence = max( [ float(result[6]) for result in results] )
        else:
            image_confidence = 0.0

        yield bboxes, confidences, image_confidence
    end_prog()
