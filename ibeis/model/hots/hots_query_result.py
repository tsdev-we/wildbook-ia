from __future__ import absolute_import, division, print_function
import utool
import utool as ut  # NOQA
# Python
import six
from six.moves import zip, cPickle
from os.path import exists, split, join
from zipfile import error as BadZipFile  # Screwy naming convention.
import os
# Scientific
import numpy as np
from ibeis.model.hots import precision_recall
from ibeis.model.hots import name_scoring
from ibeis.model.hots import exceptions as hsexcept
(print, print_, printDBG, rrr, profile) = utool.inject(__name__, '[QRes]', DEBUG=False)


#FORCE_LONGNAME = utool.get_argflag('--longname') or (not utool.WIN32 and not utool.get_argflag('--nolongname'))
MAX_FNAME_LEN = 64 if utool.WIN32 else 200
TRUNCATE_UUIDS = utool.get_argflag(('--truncate-uuids', '--trunc-uuids')) or (
    utool.is_developer() and not utool.get_argflag(('--notruncate-uuids', '--notrunc-uuids')))
VERBOSE = utool.get_argflag(('--verbose-query-result', '--verb-qres')) or ut.VERBOSE

#=========================
# Query Result Class
#=========================


def qres_get_matching_keypoints(qres, ibs, aid2_list):  # aid2 is a name. 2 != 2 to here
    aid1 = qres.qaid
    kpts1 = ibs.get_annot_kpts(aid1)
    kpts2_list = ibs.get_annot_kpts(aid2_list)
    matching_kpts_list = []
    empty_fm = np.empty((0, 2))
    for aid2, kpts2 in zip(aid2_list, kpts2_list):
        fm = qres.aid2_fm.get(aid2, empty_fm)
        if len(fm) == 0:
            continue
        kpts1_m = kpts1[fm.T[0]]
        kpts2_m = kpts2[fm.T[1]]
        kpts_match = (kpts1_m, kpts2_m)
        matching_kpts_list.append(kpts_match)
    return matching_kpts_list


def remove_corrupted_queries(qresdir, qres, dryrun=True):
    # This qres must be corrupted!
    cfgstr = qres.cfgstr
    hash_id = utool.hashstr(cfgstr)
    qres_dir  = qresdir
    testres_dir = join(qresdir, '..', 'experiment_harness_results')
    utool.remove_files_in_dir(testres_dir, dryrun=dryrun)
    utool.remove_files_in_dir(qres_dir, '*' + cfgstr + '*', dryrun=dryrun)
    utool.remove_files_in_dir(qres_dir, '*' + hash_id + '*', dryrun=dryrun)


def query_result_fpath(qresdir, qaid, qauuid, cfgstr):
    fname = query_result_fname(qaid, qauuid, cfgstr)
    fpath = join(qresdir, fname)
    return fpath


def query_result_fname(qaid, qauuid, cfgstr, ext='.npz'):
    """
    Builds a filename for a queryresult

    Args:
        qaid (int): query annotation rowid
        qauuid (uuid.UUID): query annotation unique universal id
        cfgstr (str): query parameter configuration string
        ext (str): filetype extension
    """
    #fname_fmt = 'res_{cfgstr}_qaid={qaid}_qauuid={quuid}{ext}'
    fname_fmt = 'qaid={qaid}_res_{cfgstr}_quuid={quuid}{ext}'
    quuid_str = str(qauuid)[0:8] if TRUNCATE_UUIDS else str(qauuid)
    fmt_dict = dict(cfgstr=cfgstr, qaid=qaid, quuid=quuid_str, ext=ext)
    #fname = fname_fmt.format(**fmt_dict)
    fname = utool.long_fname_format(fname_fmt, fmt_dict, ['cfgstr'], max_len=MAX_FNAME_LEN)
    # condence the filename if it is too long (grumble grumble windows)
    #if (not FORCE_LONGNAME) and len(fname) > 64:
    #if len(fname) > MAX_FNAME_LEN:
    #    hash_id = utool.hashstr(cfgstr)
    #    fname = fname_fmt.format(
    #        cfgstr=hash_id, qaid=qaid, quuid=quuid_str, ext=ext)
    return fname


def _qres_dicteq(aid2_xx1, aid2_xx2):
    """ Checks to see if qres dicts are the same """
    try:
        for (aid1, xx1), (aid2, xx2) in zip(aid2_xx1.items(),
                                            aid2_xx2.items()):
            assert aid1 == aid2, 'key mismatch'
            if np.iterable(xx1):
                assert all([np.all(x1 == x2) for (x1, x2) in zip(xx1, xx2)])
            else:
                assert xx1 == xx2
    except AssertionError:
        return False
    return True


__OBJECT_BASE__ = object  # utool.util_dev.get_object_base()


def assert_qres(qres):
    try:
        assert len(qres.aid2_fm) == len(qres.aid2_fs), 'fm and fs do not agree'
        assert len(qres.aid2_fm) == len(qres.aid2_fk), 'fm and fk do not agree'
        assert len(qres.aid2_fm) == len(qres.aid2_score), 'fm and score do not agree'
    except AssertionError as ex:
        ut.printex(ex, '[!qr]  matching dicts do not agree',
                   keys=[
                       (ut.dictinfo, 'qres.aid2_fm'),
                       (ut.dictinfo, 'qres.aid2_fs'),
                       (ut.dictinfo, 'qres.aid2_fk'),
                       (ut.dictinfo, 'qres.aid2_score'),
                   ])
        raise
    nFeatMatch_list = get_num_feats_in_matches(qres)
    assert all([num1 == num2 for (num1, num2) in
                zip(nFeatMatch_list, (len(fm) for fm in six.itervalues(qres.aid2_fm)))])
    assert all([num1 == num2 for (num1, num2) in
                zip(nFeatMatch_list, (len(fs) for fs in six.itervalues(qres.aid2_fs)))])
    assert all([num1 == num2 for (num1, num2) in
                zip(nFeatMatch_list, (len(fk) for fk in six.itervalues(qres.aid2_fk)))])


def get_num_chip_matches(qres):
    return len(qres.aid2_fm)


def get_num_feats_in_matches(qres):
    return [len(fm) for fm in six.itervalues(qres.aid2_fm)]


@six.add_metaclass(ut.ReloadingMetaclass)
class QueryResult(__OBJECT_BASE__):
    #__slots__ = ['qaid', 'qauuid', 'cfgstr', 'eid',
    #             'aid2_fm', 'aid2_fs', 'aid2_fk', 'aid2_score',
    #             'metadata']
    def __init__(qres, qaid, qauuid, cfgstr, daids):
        # THE UID MUST BE SPECIFIED CORRECTLY AT CREATION TIME
        # TODO: Merge FS and FK
        super(QueryResult, qres).__init__()
        qres.qaid = qaid
        qres.qauuid = qauuid  # query annot uuid
        # TODO: qreq.daids could easilly be a hash of the duuids in the qreq_ so
        # the daids list can be looked up instead of stored on disk for every
        # query result.
        qres.daids = daids  # matchable database chips. external_daids from qreq_. (should this be duuids?)
        #qres.qauuid = qauuid
        qres.cfgstr = cfgstr  # should have database info hashed in from qreq
        qres.eid = None  # encounter id
        # Assigned features matches
        qres.aid2_fm = None  # feat_match_list
        qres.aid2_fs = None  # feat_score_list
        qres.aid2_fk = None  # feat_rank_list
        qres.aid2_score = None  # annotation score
        qres.aid2_prob = None  # annotation normalized score
        qres.metadata = None  # messy (meta information of query)
        #qres.daid_list = None  # matchable daids

    def load(qres, qresdir, verbose=VERBOSE, force_miss=False):
        """ Loads the result from the given database """
        fpath = qres.get_fpath(qresdir)
        qaid_good = qres.qaid
        qauuid_good = qres.qauuid
        daids_good = qres.daids
        try:
            if force_miss:
                raise hsexcept.HotsCacheMissError('force miss')
            #print('[qr] qres.load() fpath=%r' % (split(fpath)[1],))
            with open(fpath, 'rb') as file_:
                loaded_dict = cPickle.load(file_)
                qres.__dict__.update(loaded_dict)
            #if not isinstance(qres.metadata, dict):
            #    print('[qr] loading old result format')
            #    qres.metadata = {}
            if verbose:
                print('... qres cache hit: %r' % (split(fpath)[1],))
        except IOError as ex:
            if not exists(fpath):
                msg = '... qres cache miss: %r' % (split(fpath)[1],)
                if verbose:
                    print(msg)
                raise hsexcept.HotsCacheMissError(msg)
            msg = '[!qr] QueryResult(qaid=%d) is corrupt' % (qres.qaid)
            utool.printex(ex, msg, iswarning=True)
            raise hsexcept.HotsNeedsRecomputeError(msg)
        except BadZipFile as ex:
            msg = '[!qr] QueryResult(qaid=%d) has bad zipfile' % (qres.qaid)
            utool.printex(ex, msg, iswarning=True)
            if exists(fpath):
                print('[qr] Removing corrupted file: %r' % fpath)
                os.remove(fpath)
                raise hsexcept.HotsNeedsRecomputeError(msg)
            else:
                raise Exception(msg)
        except (ValueError, TypeError) as ex:
            utool.printex(ex, iswarning=True)
            exstr = str(ex)
            print(exstr)
            if exstr == 'unsupported pickle protocol: 3':
                raise hsexcept.HotsNeedsRecomputeError(str(ex))
            elif exstr.startswith('("\'numpy.ndarray\' object is not callable",'):
                raise hsexcept.HotsNeedsRecomputeError(str(ex))
            raise
        except hsexcept.HotsCacheMissError:
            msg = '... qres cache miss: %r' % (split(fpath)[1],)
            if verbose:
                print(msg)
        except Exception as ex:
            utool.printex(ex, 'unknown exception while loading query result')
            raise
        assert qauuid_good == qres.qauuid
        if qres.daids is None:
            qres.daids = daids_good
        else:
            if isinstance(daids_good, np.ndarray):
                assert np.all(daids_good == qres.daids)
            else:
                assert daids_good == qres.daids
        qres.qauuid = qauuid_good
        qres.qaid = qaid_good

    def save(qres, qresdir, verbose=utool.NOT_QUIET and utool.VERBOSE):
        """ saves query result to directory """
        fpath = qres.get_fpath(qresdir)
        if verbose:
            print('[qr] cache save: %r' % (split(fpath)[1],))
        with open(fpath, 'wb') as file_:
            cPickle.dump(qres.__dict__, file_)

    def __eq__(self, other):
        """ For testing. Do not use"""
        return all([
            self.qaid == other.qaid,
            self.cfgstr == other.cfgstr,
            self.eid == other.eid,
            _qres_dicteq(self.aid2_fm, other.aid2_fm),
            _qres_dicteq(self.aid2_fs, self.aid2_fs),
            _qres_dicteq(self.aid2_fk, self.aid2_fk),
            _qres_dicteq(self.aid2_score, other.aid2_score),
            _qres_dicteq(self.metadata, other.metadata),
        ])

    def get_fpath(qres, qresdir):
        return query_result_fpath(qresdir, qres.qaid, qres.qauuid, qres.cfgstr)

    def has_cache(qres, qresdir):
        return exists(qres.get_fpath(qresdir))

    def get_fname(qres, **kwargs):
        return query_result_fname(qres.qaid, qres.qauuid, qres.cfgstr, **kwargs)

    def cache_bytes(qres, qresdir):
        """ Size of the cached query result on disk """
        fpath  = qres.get_fpath(qresdir)
        nBytes = utool.file_bytes(fpath)
        return nBytes

    # ----------------------------------------

    def get_nscoretup(qres, ibs):
        aid_list, score_list = qres.get_aids_and_scores(name_scoring=False)
        nscoretup = name_scoring.get_one_score_per_name(ibs, aid_list, score_list)
        # (sorted_nids, sorted_nscore, sorted_aids, sorted_scores) = nscoretup
        return nscoretup

    def get_aids_and_scores(qres, name_scoring=False, ibs=None):
        """ returns a chip index list and associated score list """
        if name_scoring:
            assert ibs is not None, 'must specify ibs for name_scoring'
            nscoretup = qres.get_nscoretup(ibs)
            (sorted_nids, sorted_nscore, sorted_aids, sorted_scores) = nscoretup
            score_arr = np.array(sorted_nscore)
            aid_arr = np.array(ut.get_list_column(sorted_aids, 0))
        else:
            if qres.aid2_prob is None:
                aid_arr   = np.array(list(qres.aid2_score.keys()), dtype=np.int32)
                score_arr = np.array(list(qres.aid2_score.values()), dtype=np.float64)
            else:
                aid_arr   = np.array(list(qres.aid2_prob.keys()), dtype=np.int32)
                score_arr = np.array(list(qres.aid2_prob.values()), dtype=np.float64)
        return aid_arr, score_arr

    def get_aid_scores(qres, aid_arr, fillvalue=None, rawscore=False):
        if rawscore or qres.aid2_prob is None:
            return [qres.aid2_score.get(aid, fillvalue) for aid in aid_arr]
        else:
            return [qres.aid2_prob.get(aid, fillvalue) for aid in aid_arr]

    # ----------------------------------------

    def get_sorted_nids_and_scores(qres, ibs):
        nscoretup = qres.get_nscoretup(ibs)
        (sorted_nids, sorted_nscores, sorted_aids, sorted_scores)  = nscoretup
        return sorted_nids, sorted_nscores

    def get_name_decisiontup(qres, ibs):
        sorted_nids, sorted_nscores = qres.get_sorted_nids_and_scores(ibs)
        if len(sorted_nids) == 0:
            return (None, None)
        else:
            nid = sorted_nids[0]
            nscore = sorted_nscores[0]
            return (nid, nscore)

    def get_top_aids(qres, num=None, name_scoring=False, ibs=None):
        """ Returns a ranked list of chip indexes """
        # TODO: rename num to ranks_lt
        aid_arr, score_arr = qres.get_aids_and_scores(name_scoring=name_scoring,
                                                      ibs=ibs)
        # Get chip-ids sorted by scores
        top_aids = aid_arr[score_arr.argsort()[::-1]]
        num_indexed = len(top_aids)
        if num is None:
            num = num_indexed
        return top_aids[0:min(num, num_indexed)]

    @utool.accepts_scalar_input
    def get_aid_ranks(qres, aid_arr, fillvalue=None):
        """ get ranks of annotation ids """
        if isinstance(aid_arr, (tuple, list)):
            aid_arr = np.array(aid_arr)
        top_aids = qres.get_top_aids()
        foundpos = [np.where(top_aids == aid)[0] for aid in aid_arr]
        ranks_   = [ranks if len(ranks) > 0 else [fillvalue]
                    for ranks in foundpos]
        assert all([len(ranks) == 1 for ranks in ranks_]), (
            'len(aid_ranks) != 1')
        rank_list = [ranks[0] for ranks in ranks_]
        return rank_list

    def get_aid_truth(qres, ibs, aid_list):
        # 0: false, 1: True, 2: unknown
        isgt_list = [ibs.get_match_truth(qres.qaid, aid) for aid in aid_list]
        return isgt_list

    # ----------------------------------------

    def get_daids(qres):
        """ returns database annotation ids this query was run with """
        # TODO: possibly look this up in a more space efficient way
        return qres.daids

    def get_qaid(qres):
        """ returns query database annotation id """
        return qres.qaid

    def get_matching_keypoints(qres, ibs, aid2_list):
        return qres_get_matching_keypoints(qres, ibs, aid2_list)

    def is_nsum(qres):
        return 'AGG(nsum)' in qres.cfgstr and ',nsum,' in qres.cfgstr

    def get_fmatch_index(qres, aid, qfx):
        """ Returns the feature index in aid matching the query's qfx-th feature
            (if it exists)
        """
        fm = qres.aid2_fm[aid]
        mx_list = np.where(fm[:, 0] == qfx)[0]
        if len(mx_list) != 1:
            raise IndexError('[!qr] qfx=%r not found' % (qfx))
        else:
            mx = mx_list[0]
            return mx

    def get_worse_possible_rank(qres):
        """ a good non None value to use for None ranks """
        #worse_possible_rank = max(len(qres.get_daids()) + 2, 9001)
        worse_possible_rank = len(qres.get_daids()) + 1
        return worse_possible_rank

    def get_classified_pos(qres):
        top_aids = np.array(qres.get_top_aids())
        pos_aids = top_aids[0:1]
        return pos_aids

    # ----------------------------------------

    def get_groundfalse_aids(qres, ibs):
        assert ibs is not None, 'must pass in valid ibs controller'
        gf_aids = ibs.get_annot_groundfalse(qres.get_qaid(), daid_list=qres.get_daids())
        return gf_aids

    def get_groundtruth_aids(qres, ibs):
        """
        returns the groundtruth with respect to what could have been matched for
        this query
        """
        assert ibs is not None, 'must pass in valid ibs controller'
        gt_aids = ibs.get_annot_groundtruth(qres.get_qaid(), daid_list=qres.get_daids())
        return gt_aids

    def get_gt_scores(qres, gt_aids=None, ibs=None, return_gtaids=False):
        """ returns groundfalse scores """
        # Ensure correct input
        if gt_aids is None and ibs is None:
            raise Exception('[qr] must pass in the gt_aids or ibs object')
        if gt_aids is None:
            gt_aids = qres.get_groundtruth_aids(ibs)
        gt_scores = qres.get_aid_scores(gt_aids)
        if return_gtaids:
            return gt_scores, gt_aids
        else:
            return gt_scores

    def get_gf_scores(qres, gf_aids=None, ibs=None, return_gfaids=False):
        """ returns groundfalse scores """
        # Ensure correct input
        if gf_aids is None and ibs is None:
            raise Exception('[qr] must pass in the gf_aids or ibs object')
        if gf_aids is None:
            gf_aids = qres.get_groundfalse_aids(ibs)
        gf_scores = qres.get_aid_scores(gf_aids)
        if return_gfaids:
            return gf_scores, gf_aids
        else:
            return gf_scores

    def get_gt_ranks(qres, gt_aids=None, ibs=None, return_gtaids=False, fillvalue=None):
        """ returns the 0 indexed ranking of each groundtruth chip """
        # Ensure correct input
        if gt_aids is None and ibs is None:
            raise Exception('[qr] must pass in the gt_aids or ibs object')
        if gt_aids is None:
            gt_aids = qres.get_groundtruth_aids(ibs)
        gt_ranks = qres.get_aid_ranks(gt_aids, fillvalue=fillvalue)
        if return_gtaids:
            return gt_ranks, gt_aids
        else:
            return gt_ranks

    def get_best_gt_rank(qres, ibs=None, gt_aids=None):
        """ Returns the best rank over all the groundtruth """
        gt_ranks, gt_aids = qres.get_gt_ranks(ibs=ibs, gt_aids=gt_aids, return_gtaids=True)
        aidrank_tups = list(zip(gt_aids, gt_ranks))
        # Get only the aids that placed in the shortlist
        #valid_gtaids = np.array([ aid for aid, rank in aidrank_tups if rank is not None])
        valid_ranks  = np.array([rank for aid, rank in aidrank_tups if rank is not None])
        # Sort so lowest score is first
        best_rankx = valid_ranks.argsort()
        #best_gtaids  = best_gtaids[best_rankx]
        best_gtranks = valid_ranks[best_rankx]
        if len(best_gtranks) == 0:
            best_rank = -1
        else:
            best_rank = best_gtranks[0]
        return best_rank

    # ----------------------------------------

    def get_average_percision(qres, ibs=None, gt_aids=None):
        return precision_recall.get_average_percision_(qres, ibs=ibs, gt_aids=gt_aids)

    def get_interpolated_precision_vs_recall(qres, ibs=None, gt_aids=None):
        return precision_recall.get_interpolated_precision_vs_recall_(qres, ibs=ibs, gt_aids=gt_aids)

    def show_precision_recall_curve(qres, ibs=None, gt_aids=None, fnum=1):
        return precision_recall.show_precision_recall_curve_(qres, ibs=ibs, gt_aids=gt_aids, fnum=fnum)

    def get_precision_recall_curve(qres, ibs=None, gt_aids=None):
        return precision_recall.get_precision_recall_curve_(qres, ibs=ibs, gt_aids=gt_aids)

    # ----------------------------------------

    def get_match_tbldata(qres, ranks_lt=5, name_scoring=False, ibs=None):
        """
        Returns matchinfo in table format (qaids, aids, scores, ranks)
        """
        # TODO: get rid of conflict with module name name_scoring
        aid_arr, score_arr = qres.get_aids_and_scores(name_scoring=name_scoring, ibs=ibs)
        # Sort the scores in rank order
        sortx     = score_arr.argsort()[::-1]
        score_arr = score_arr[sortx]
        aid_arr   = aid_arr[sortx]
        rank_arr  = np.arange(sortx.size)
        # Return only rows where rank < ranks_lt
        isvalid = rank_arr < ranks_lt
        aids    =   aid_arr[isvalid]
        scores  = score_arr[isvalid]
        ranks   =  rank_arr[isvalid]
        qaids   = np.full(aids.shape, qres.qaid, dtype=aids.dtype)
        tbldata = (qaids, aids, scores, ranks)
        # DEBUG
        #column_lbls = ['qaids', 'aids', 'scores', 'ranks']
        #qaid_arr      = np.full(aid_arr.shape, qres.qaid, dtype=aid_arr.dtype)
        #tbldata2      = (qaid_arr, aid_arr, score_arr, rank_arr)
        #print(utool.make_csv_table(tbldata, column_lbls))
        #print(utool.make_csv_table(tbldata2, column_lbls))
        #utool.embed()
        return tbldata

    def get_inspect_str(qres, ibs=None, name_scoring=False):
        assert_qres(qres)
        nFeatMatch_list = get_num_feats_in_matches(qres)
        nFeatMatch_stats = utool.get_stats(nFeatMatch_list)

        top_lbls = [' top aids', ' scores', ' ranks']

        top_aids   = np.array(qres.get_top_aids(num=5, name_scoring=name_scoring, ibs=ibs), dtype=np.int32)
        top_scores = np.array(qres.get_aid_scores(top_aids), dtype=np.float64)
        top_ranks  = np.array(qres.get_aid_ranks(top_aids), dtype=np.int32)
        top_list   = [top_aids, top_scores, top_ranks]

        if ibs is not None:
            top_lbls += [' isgt']
            istrue = qres.get_aid_truth(ibs, top_aids)
            top_list.append(np.array(istrue, dtype=np.int32))
        if name_scoring:
            top_lbls = ['top nid'] + top_lbls
            top_list = [ibs.get_annot_name_rowids(top_aids)] + top_list

        top_stack = np.vstack(top_list)
        top_stack = np.array(top_stack, dtype=object)
        #np.int32)
        top_str = str(top_stack)

        top_lbl = '\n'.join(top_lbls)
        inspect_list = ['QueryResult',
                        qres.cfgstr,
                        ]
        if ibs is not None:
            gt_ranks  = qres.get_gt_ranks(ibs=ibs)
            gt_scores = qres.get_gt_scores(ibs=ibs)
            inspect_list.append('gt_ranks = %r' % gt_ranks)
            inspect_list.append('gt_scores = %r' % gt_scores)

        inspect_list.extend([
            'qaid=%r ' % qres.qaid,
            utool.hz_str(top_lbl, ' ', top_str),
            'num Feat Matches stats:',
            utool.indent(utool.dict_str(nFeatMatch_stats)),
        ])

        inspect_str = '\n'.join(inspect_list)

        inspect_str = utool.indent(inspect_str, '[INSPECT] ')
        return inspect_str

    # ----------------------------------------

    def make_smaller_title(qres, remove_daids=True, remove_chip=True,
                           remove_feat=True):
        return qres.make_title(remove_daids=remove_daids,
                               remove_chip=remove_chip,
                               remove_feat=remove_feat)

    def make_title(qres, pack=False, remove_daids=False, remove_chip=False,
                   remove_feat=False, textwidth=80):
        cfgstr = qres.cfgstr

        def parse_remove(format_, string_):
            import parse
            # TODO: move to utool
            # Do padding so prefix or suffix could be empty
            pad_format_ = '{prefix}' + format_ + '{suffix}'
            pad_string_ = '_' + string_ + '_'
            parse_result = parse.parse(pad_format_, pad_string_)
            new_string = parse_result['prefix'][1:] + parse_result['suffix'][:-1]
            return new_string, parse_result

        if remove_daids:
            cfgstr, _ = parse_remove('_DAIDS(({daid_shape}){daid_hash})', cfgstr)
        if remove_chip:
            cfgstr, _ = parse_remove('_CHIP({chip_cfgstr})', cfgstr)
        if remove_feat:
            cfgstr, _ = parse_remove('_FEAT({feat_cfgstr})', cfgstr)

        if pack:
            # Separate into newlines if requested (makes it easier to fit on screen)
            cfgstr = ut.packstr(cfgstr, textwidth=textwidth, break_words=False, breakchars='_', wordsep='_')

        component_list = [
            'qaid={qaid} '.format(qaid=qres.qaid),
            #'qauuid={qauuid}'.format(qauuid=qres.qauuid),
            'cfgstr={cfgstr}'.format(cfgstr=cfgstr),
        ]
        title_str = ''.join(component_list)
        return title_str

    # ----------------------------------------

    #TODO?: @utool.augment_signature(viz_qres.show_qres_top)
    def show_top(qres, ibs, *args, **kwargs):
        from ibeis.viz import viz_qres
        return viz_qres.show_qres_top(ibs, qres, *args, **kwargs)

    def show_analysis(qres, ibs, *args, **kwargs):
        from ibeis.viz import viz_qres
        return viz_qres.show_qres_analysis(ibs, qres, *args, **kwargs)

    def ishow_top(qres, ibs, *args, **kwargs):
        from ibeis.viz.interact import interact_qres
        return interact_qres.ishow_qres(ibs, qres, *args, **kwargs)

    def qt_inspect_gui(qres, ibs, ranks_lt=5, name_scoring=False):
        from ibeis.gui import inspect_gui
        import guitool
        guitool.ensure_qapp()
        qaid2_qres = {qres.qaid: qres}
        print('[inspect_matches] make_qres_widget')
        qres_wgt = inspect_gui.QueryResultsWidget(ibs, qaid2_qres,
                                                  ranks_lt=ranks_lt,
                                                  name_scoring=name_scoring)
        print('[inspect_matches] show')
        qres_wgt.show()
        print('[inspect_matches] raise')
        qres_wgt.raise_()
        return qres_wgt

    def show(qres, ibs, type_, *args, **kwargs):
        if type_ == 'top':
            return qres.show_top(ibs, *args, **kwargs)
        elif type_ == 'analysis':
            return qres.show_analysis(ibs, *args, **kwargs)
        else:
            raise AssertionError('Uknown type=%r' % type_)


if __name__ == '__main__':
    r"""
    TODO:
        * Remove all nonmethod calls to qres
          Find them with this:
              rob gp 'qres\\.[A-Za-z_][A-Za-z0-9_]*\\b[^(]'
        * Do not store results in dicts. use ndarrays

    CommandLine:
        python -c "import utool, ibeis.model.hots.hots_query_result; utool.doctest_funcs(ibeis.model.hots.hots_query_result, allexamples=True)"
        python -c "import utool, ibeis.model.hots.hots_query_result; utool.doctest_funcs(ibeis.model.hots.hots_query_result)"
        python -m ibeis.model.hots.hots_query_result
        python -m ibeis.model.hots.hots_query_result --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
