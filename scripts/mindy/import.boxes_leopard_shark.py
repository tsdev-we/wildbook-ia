# -*- coding: utf-8 -*-
"""
Render Mindy annotation data for leopard shark data.

pip install xmltodict
"""
from os.path import exists, join

import numpy as np
import utool as ut
import xmltodict
from PIL import ExifTags, Image

import wbia

ibs = wbia.opendb(dbdir='/data/db')


with open('annotations.xml', 'r') as xml_file:
    data = xmltodict.parse(xml_file.read())

annotations = data.get('annotations', [])
version = annotations.get('version')
meta = annotations.get('meta')
images = annotations.get('image')

print('Using annotation tool version {}'.format(version))
print('Exported on {}'.format(meta.get('dumped')))
print('Task:')
print(ut.repr3(meta.get('task')))

add_paths = []
add_orients = []
add_bboxes = []
add_thetas = []
add_label = []
add_species = []
viewpoints = []

for image in images:
    filename = image.get('@name')
    if "right" in filename.lower():
        viewpoint = "right"
    elif "extractr" in filename.lower():
        viewpoint = "right"
    elif "extract" in filename.lower():
        viewpoint = "left"
    elif "left" in filename.lower():
        viewpoint = "left"
    elif "lhs" in filename.lower():
        viewpoint = "left"
    elif "rhs" in filename.lower():
        viewpoint = "right"
    else:
        viewpoint = "None"
    bbox = image.get('box')
    if type(bbox) == list:
        bbox = dict(bbox[0])
    assert type(bbox) == dict
    label = bbox.get('@label')

    xtl = int(np.around(float(bbox.get('@xtl'))))
    ytl = int(np.around(float(bbox.get('@ytl'))))
    xbr = int(np.around(float(bbox.get('@xbr'))))
    ybr = int(np.around(float(bbox.get('@ybr'))))
    rotation = float(bbox.get('@rotation', 0.0))

    filepath = join('images', filename)

    assert exists(filepath)
    img = Image.open(filepath)
    exif_raw = img._getexif()
    if exif_raw is None:
        exif_raw = {}
    globals().update(locals())
    exif = {ExifTags.TAGS[k]: v for k, v in exif_raw.items() if k in ExifTags.TAGS}
    orient = exif.get('Orientation', None)
    img.close()

    bbox = (xtl, ytl, xbr - xtl, ybr - ytl)
    theta = (rotation / 360.0) * (2.0 * np.pi)

    add_paths.append(filepath)
    add_orients.append(orient)
    add_bboxes.append(bbox)
    add_thetas.append(theta)
    add_label.append(label)
    viewpoints.append(viewpoint)
    add_species.append("leopard_shark")

add_gids = ibs.add_images(add_paths)

assert len(add_bboxes) == len(add_gids)
assert len(add_thetas) == len(add_gids)
assert len(add_species) == len(add_gids)
assert len(add_label) == len(add_gids)


def remove_nones(list1, list2):
    """*summary: Takes two lists and removes values that are nones based on list1
    """
    list_a = [val for val in list1 if val is not None]
    list_b = [val for i, val in enumerate(list2) if list1[i] is not None]
    return list_a, list_b


add_orient_without_nones, add_gids_without_nones = remove_nones(add_orients, add_gids)

ibs.set_image_orientation(add_gids_without_nones, add_orient_without_nones)


matching_add_gids, matching_bbox_list = remove_nones(add_gids, add_bboxes)
_, matching_theta_list = remove_nones(add_gids, add_thetas)
_, matching_viewpoints = remove_nones(add_gids, viewpoints)
_, matching_add_species = remove_nones(add_gids, add_species)

add_aids = ibs.add_annots(
    matching_add_gids,
    bbox_list=matching_bbox_list,
    theta_list=matching_theta_list,
    viewpoint_list=matching_viewpoints,
)

ibs.set_annot_species(matching_add_gids, matching_add_species)
ibs.set_annot_yaw_texts(add_aids, add_label)
ibs.precompute_web_viewpoint_thumbnails()
ibs.get_annot_viewpoints()
