from __future__ import absolute_import, division, print_function
import numpy as np
import cv2
import utool
import drawtool.draw_func2 as df2
from vtool import image as gtool
from . import viz_helpers as vh
(print, print_, printDBG, rrr, profile) = utool.inject(__name__, '[viz_misc]', DEBUG=False)


@utool.indent_func
def viz_sv(chip1, chip2, kpts1, kpts2, fm, H, inliers, Aff, aff_inliers, fnum=1):
    print('warp homog')
    wh2 = gtool.get_size(chip2)
    chip1_Ht = cv2.warpPerspective(chip1, H, wh2)
    print('warp affine')
    chip1_At = cv2.warpAffine(chip1, Aff[0:2, :], wh2)
    chip2_blendA = np.zeros(chip2.shape, dtype=chip2.dtype)
    chip2_blendH = np.zeros(chip2.shape, dtype=chip2.dtype)
    chip2_blendA = chip2 / 2 + chip1_At / 2
    chip2_blendH = chip2 / 2 + chip1_Ht / 2

    df2.figure(fnum=fnum, pnum=(3, 4, 1), docla=True, doclf=True)

    def _draw_chip(title, chip, px, *args, **kwargs):
        df2.imshow(chip, *args, title=title, fnum=fnum, pnum=(3, 4, px), **kwargs)

    # Draw original matches, affine inliers, and homography inliers
    def _draw_matches(title, fm, px):
        # Helper with common arguments to df2.show_chipmatch2
        dmkwargs = dict(fs=None, title=title, all_kpts=False, draw_lines=True,
                        docla=True, fnum=fnum, pnum=(3, 3, px))
        df2.show_chipmatch2(chip1, chip2, kpts1, kpts2, fm, **dmkwargs)

    # Draw the Assigned -> Affine -> Homography matches
    assign_fm = fm
    affine_fm = fm[aff_inliers]
    homog_fm = fm[inliers]
    _draw_matches('%d Assigned matches' % len(assign_fm), assign_fm, 1)
    _draw_matches('%d Affine inliers' % len(affine_fm), affine_fm,   2)
    _draw_matches('%d Homography inliers' % len(homog_fm), homog_fm, 3)
    # Draw the Affine Transformations
    _draw_chip('Source', chip1, 5)
    _draw_chip('Affine', chip1_At, 6)
    _draw_chip('Destination', chip2, 7)
    _draw_chip('Aff Blend', chip2_blendA, 8)
    # Draw the Homography Transformation
    _draw_chip('Source', chip1, 9)
    _draw_chip('Homog', chip1_Ht, 10)
    _draw_chip('Destination', chip2, 11)
    _draw_chip('Homog Blend', chip2_blendH, 12)


@utool.indent_func
def show_sv(ibs, cid1, cid2, chipmatch_FILT, cid2_svtup, **kwargs):
    print('\n[viz] ======================')
    chip1, chip2 = vh.get_chips(ibs, [cid1, cid2], **kwargs)
    kpts1, kpts2 = vh.get_kpts(ibs, [cid1, cid2], **kwargs)
    cid2_fm, cid2_fs, cid2_fk = chipmatch_FILT
    fm = cid2_fm[cid2]
    (H, inliers, Aff, aff_inliers) = cid2_svtup[cid2]
    viz_sv(chip1, chip2, kpts1, kpts2, fm,
           H, inliers, Aff, aff_inliers, **kwargs)
