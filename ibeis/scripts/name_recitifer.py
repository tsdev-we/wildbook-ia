# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut


def reasign_names1(ibs, aid_list=None, old_img2_names=None, common_prefix=''):
    r"""
    Changes the names in the IA-database to correspond to an older naming
    convention.  If splits and merges were preformed tries to find the
    maximally consistent renaming scheme.

    Notes:
        For each annotation:
        * get the image
        * get the image full path
        * strip the full path down to the file name prefix:
             [ example /foo/bar/pic.jpg -> pic ]
        * make the name of the individual associated with that annotation be the
          file name prefix
        * save the new names to the image analysis database
        * wildbook will make a request to get all of the annotations, image
          file names, image names and animal ids

    CommandLine:
        python -m ibeis.scripts.name_recitifer rectify_names --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> aid_list = None
        >>> common_prefix = ''
        >>> old_img2_names = None #['img_fred.png', ']
        >>> result = reasign_names1(ibs, aid_list, img_list, name_list)
    """
    if aid_list is None:
        aid_list = ibs.get_valid_aids()
    # Group annotations by their current IA-name
    nid_list = ibs.get_annot_name_rowids(aid_list)
    nid2_aids = ut.group_items(aid_list, nid_list)
    unique_nids = list(nid2_aids.keys())
    grouped_aids = list(nid2_aids.values())

    # Get grouped images
    grouped_imgnames = ibs.unflat_map(ibs.get_annot_image_names, grouped_aids)

    # Assume a mapping from old image names to old names is given.
    # Or just hack it in the Lewa case.
    if old_img2_names is None:
        def get_name_from_gname(gname):
            from os.path import splitext
            gname_, ext = splitext(gname)
            assert gname_.startswith(common_prefix), (
                'prefix assumption is invalidated')
            gname_ = gname_[len(common_prefix):]
            return gname_
        # Create mapping from image name to the desired "name" for the image.
        old_img2_names = {gname: get_name_from_gname(gname)
                          for gname in ut.flatten(grouped_imgnames)}

    # Make the name of the individual associated with that annotation be the
    # file name prefix
    grouped_oldnames = [ut.take(old_img2_names, gnames)
                        for gnames in grouped_imgnames]

    # The task is now to map each name in unique_nids to one of these names
    # subject to the contraint that each name can only be used once.  This is
    # solved using a maximum bipartite matching. The new names are the left
    # nodes, the old name are the right nodes, and grouped_oldnames definse the
    # adjacency matrix.
    # NOTE: In rare cases it may be impossible to find a correct labeling using
    # only old names.  In this case new names will be created.
    new_name_text = find_consistent_labeling(grouped_oldnames)

    dry = False
    if not dry:
        # Save the new names to the image analysis database
        ibs.set_name_texts(unique_nids, new_name_text)


def reasign_names2(ibs, gname_name_pairs, aid_list=None):
    """

    Notes:
        * Given a list of pairs:  image file names (full path), animal name.
        * Go through all the images in the database and create a dictionary
        that associates the file name (full path) of the image in the database
        with the
          annotation or annotations associated with that image.
        * Go through the list of pairs:
          For each image file name, look up in the dictionary the image file
          name and assign the annotation associated with the image file name
          the animal name
        * Throughout this, keep a list of annotations that have been changed
        * Wildbook will issue a pull request to get these annotation.

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> aid_list = None
        >>> common_prefix = ''
        >>> gname_name_pairs = [
        >>>     ('easy1.JPG', 'easy'),
        >>>     ('easy2.JPG', 'easy'),
        >>>     ('easy3.JPG', 'easy'),
        >>>     ('hard1.JPG', 'hard')
        >>> ]
        >>> changed_pairs = reasign_names2(gname_name_pairs)
    """
    from os.path import basename
    if aid_list is None:
        aid_list = ibs.get_valid_aids()
    annot_gnames = ibs.get_annot_image_names(aid_list)
    # Other image name getters that may be useful
    # ibs.get_annot_image_paths(aid_list)
    # ibs.get_image_uris_original(ibs.get_annot_gids(aid_list))
    gname2_aids = ut.group_items(aid_list, annot_gnames)

    changed_aids = []
    changed_names = []

    for gname, name in gname_name_pairs:
        # make sure its just the last part of the name.
        # Ignore preceding path
        gname = basename(gname)
        aids = gname2_aids[gname]
        texts = ibs.get_annot_name_texts(aids)
        flags = [text != name for text in texts]
        aids_ = ut.compress(aids, flags)
        if len(aids_):
            changed_aids.extend(aids_)
            changed_names.extend([name] * len(aids_))

    dry = False
    if not dry:
        # Save the new names to the image analysis database
        ibs.set_annot_name_texts(changed_aids, changed_names)

    # Returned list tells you who was changed.
    changed_pairs = list(zip(changed_names, changed_aids))
    return changed_pairs


def testdata_oldnames(n_incon_groups=10, n_con_groups=2, n_per_con=5,
                      n_per_incon=5, con_sep=4, n_empty_groups=0):
    import numpy as np
    rng = np.random.RandomState(42)

    rng.randint(1, con_sep + 1)

    n_incon_labels = rng.randint(0, n_incon_groups + 1)
    incon_labels = list(range(n_incon_labels))
    con_labels = list(range(n_incon_labels, n_incon_labels + n_con_groups))

    # Build up inconsistent groups that may share labels with other groups
    n_per_incon_list = [rng.randint(min(2, n_per_incon), n_per_incon + 1)
                        for _ in range(n_incon_groups)]
    incon_groups = [
        rng.choice(incon_labels, n, replace=True).tolist()
        for n in n_per_incon_list
    ]

    # Build up consistent groups that may have multiple lables, but does not
    # share labels with any other group
    con_groups = []
    offset = n_incon_labels + 1
    for _ in range(n_con_groups):
        this_n_per = rng.randint(1, n_per_con + 1)
        this_n_avail = rng.randint(1, con_sep + 1)
        this_avail_labels = list(range(offset, offset + this_n_avail))
        this_labels = rng.choice(this_avail_labels, this_n_per, replace=True)
        con_groups.append(this_labels.tolist())
        offset += this_n_avail

    empty_groups = [[] for _ in range(n_empty_groups)]

    grouped_oldnames = incon_groups + con_groups + empty_groups
    # rng.shuffle(grouped_oldnames)
    return grouped_oldnames



def find_consistent_labeling(grouped_oldnames, verbose=False):
    """
    Solves a a maximum bipirtite matching problem to find a consistent
    name assignment.

    Args:
        gropued_oldnames (list): A group of old names where the grouping is
            based on new names. For instance:

                Given:
                    aids      = [1, 2, 3, 4, 5]
                    old_names = [0, 1, 1, 1, 0]
                    new_names = [0, 0, 1, 1, 0]

                The grouping is
                    [[0, 1, 0], [1, 1]]

                This lets us keep the old names in a split case and
                re-use exising names and make minimal changes to
                current annotation names while still being consistent
                with the new and improved grouping.

                The output will be:
                    [0, 1]

                Meaning that all annots in the first group are assigned the
                name 0 and all annots in the second group are assigned the name
                1.

    References:
        http://stackoverflow.com/questions/1398822/assignment-problem-numpy

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = [['a', 'b'], ['b', 'c'], ['c', 'a', 'a']]
        >>> new_names = find_consistent_labeling(grouped_oldnames)
        >>> print(new_names)
        [u'b', u'c', u'a']

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = testdata_oldnames(25, 15,  5, n_per_incon=5)
        >>> new_names = find_consistent_labeling(grouped_oldnames, verbose=1)
        >>> grouped_oldnames = testdata_oldnames(0, 15,  5, n_per_incon=1)
        >>> new_names = find_consistent_labeling(grouped_oldnames, verbose=1)
        >>> grouped_oldnames = testdata_oldnames(0, 0, 0, n_per_incon=1)
        >>> new_names = find_consistent_labeling(grouped_oldnames, verbose=1)

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> ydata = []
        >>> xdata = list(range(10, 750, 50))
        >>> for x in xdata:
        >>>     print('x = %r' % (x,))
        >>>     grouped_oldnames = testdata_oldnames(x, 15,  5, n_per_incon=5)
        >>>     t = ut.Timerit(3, verbose=1)
        >>>     for timer in t:
        >>>         with timer:
        >>>             new_names = find_consistent_labeling(grouped_oldnames)
        >>>     ydata.append(t.ave_secs)
        >>> ut.quit_if_noshow()
        >>> import plottool as pt
        >>> pt.qtensure()
        >>> pt.multi_plot(xdata, [ydata])
        >>> ut.show_if_requested()

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = [['a', 'b', 'c'], ['b', 'c'], ['c', 'e', 'e']]
        >>> new_names = find_consistent_labeling(grouped_oldnames)
        >>> print(new_names)
        [u'a', u'b', u'e']

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = [['a', 'b'], ['a', 'a', 'b'], ['a']]
        >>> new_names = find_consistent_labeling(grouped_oldnames)
        >>> print(new_names)
        [u'a', u'b', u'e']

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = [['a', 'b'], ['e'], ['a', 'a', 'b'], [], ['a'], ['d']]
        >>> new_names = find_consistent_labeling(grouped_oldnames)
        >>> print(new_names)
        [u'a', u'b', u'e']

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.scripts.name_recitifer import *  # NOQA
        >>> grouped_oldnames = [[], ['a', 'a'], [],
        >>>                     ['a', 'a', 'a', 'a', 'a', 'a', 'a', 'b'], ['a']]
        >>> new_names = find_consistent_labeling(grouped_oldnames)
        >>> print(new_names)
        [u'_extra_name0', u'a', u'_extra_name1', u'b', u'_extra_name2']
    """
    import numpy as np
    import scipy.optimize

    unique_old_names = ut.unique(ut.flatten(grouped_oldnames))

    # TODO: find names that are only used once, and just ignore those for
    # optimization.
    unique_set = set(unique_old_names)
    oldname_sets = list(map(set, grouped_oldnames))
    usage_hist = ut.dict_hist(ut.flatten(oldname_sets))
    conflicts = {k for k, v in usage_hist.items() if v > 1}
    nonconflicts = {k for k, v in usage_hist.items() if v == 1}

    conflict_groups = []
    orig_idxs = []
    assignment = [None] * len(grouped_oldnames)
    ntrivial = 0
    for idx, group in enumerate(grouped_oldnames):
        if set(group).intersection(conflicts):
            orig_idxs.append(idx)
            conflict_groups.append(group)
        else:
            ntrivial += 1
            if len(group) > 0:
                h = ut.dict_hist(group)
                hitems = list(h.items())
                hvals = [i[1] for i in hitems]
                maxval = max(hvals)
                g = min([k for k, v in hitems if v == maxval])
                assignment[idx] = g
            else:
                assignment[idx] = None

    if verbose:
        print('rectify %d non-trivial groups' % (len(conflict_groups),))
        print('rectify %d trivial groups' % (ntrivial,))

    num_extra = 0

    if len(conflict_groups) > 0:
        grouped_oldnames_ = conflict_groups
        unique_old_names = ut.unique(ut.flatten(grouped_oldnames_))
        num_new_names = len(grouped_oldnames_)
        num_old_names = len(unique_old_names)
        extra_oldnames = []

        # Create padded dummy values.  This accounts for the case where it is
        # impossible to uniquely map to the old db
        num_extra = num_new_names - num_old_names
        if num_extra > 0:
            extra_oldnames = ['_extra_name%d' % (count,) for count in
                              range(num_extra)]
        elif num_extra < 0:
            pass
        else:
            extra_oldnames = []
        assignable_names = unique_old_names + extra_oldnames

        total = len(assignable_names)

        # Allocate assignment matrix
        # Start with a large negative value indicating
        # that you must select from your assignments only
        profit_matrix = -np.ones((total, total), dtype=np.int) * (2 * total)
        # Populate assignment profit matrix
        oldname2_idx = ut.make_index_lookup(assignable_names)
        name_freq_list = [ut.dict_hist(names) for names in grouped_oldnames_]
        # Initialize base profit for using a previously used name
        for rowx, name_freq in enumerate(name_freq_list):
            for name, freq in name_freq.items():
                colx = oldname2_idx[name]
                profit_matrix[rowx, colx] = 1
        # Now add in the real profit
        for rowx, name_freq in enumerate(name_freq_list):
            for name, freq in name_freq.items():
                colx = oldname2_idx[name]
                profit_matrix[rowx, colx] += freq
        # Set a small profit for using an extra name
        extra_colxs = ut.take(oldname2_idx, extra_oldnames)
        profit_matrix[:, extra_colxs] = 1

        # Convert to minimization problem
        big_value = (profit_matrix.max()) - (profit_matrix.min())
        cost_matrix = big_value - profit_matrix

        # Don't use munkres, it is pure python and very slow. Use scipy instead
        indexes = list(zip(*scipy.optimize.linear_sum_assignment(cost_matrix)))

        # Map output to be aligned with input
        rx2_cx = dict(indexes)
        assignment_ = [assignable_names[rx2_cx[rx]]
                       for rx in range(num_new_names)]

        # Reintegrate trivial values
        for idx, g in zip(orig_idxs, assignment_):
            assignment[idx] = g

    for idx, val in enumerate(assignment):
        if val is None:
            assignment[idx] = '_extra_name%d' % (num_extra,)
            num_extra += 1
    return assignment
