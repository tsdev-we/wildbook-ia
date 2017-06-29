# -*- coding: utf-8 -*-
"""
TODO: separate out the tests and make this file just generate the demo data
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import itertools as it
import numpy as np
import utool as ut
from ibeis.algo.graph.state import POSTV, NEGTV, INCMP, UNREV
from ibeis.algo.graph.state import SAME, DIFF, NULL  # NOQA
print, rrr, profile = ut.inject2(__name__)


def make_dummy_infr(annots_per_name):
    import ibeis
    nids = [val for val, num in enumerate(annots_per_name, start=1)
            for _ in range(num)]
    aids = range(len(nids))
    infr = ibeis.AnnotInference(None, aids, nids=nids, autoinit=True,
                                verbose=1)
    return infr


def demodata_mtest_infr(state='empty'):
    import ibeis
    ibs = ibeis.opendb(db='PZ_MTEST')
    annots = ibs.annots()
    names = list(annots.group_items(annots.nids).values())
    ut.shuffle(names, rng=321)
    test_aids = ut.flatten(names[1::2])
    infr = ibeis.AnnotInference(ibs, test_aids, autoinit=True)
    infr.reset(state=state)
    return infr


def demodata_infr2(defaultdb='PZ_MTEST'):
    defaultdb = 'PZ_MTEST'
    import ibeis
    ibs = ibeis.opendb(defaultdb=defaultdb)
    annots = ibs.annots()
    names = list(annots.group_items(annots.nids).values())[0:20]
    def dummy_phi(c, n):
        x = np.arange(n)
        phi = c * x / (c * x + 1)
        phi = phi / phi.sum()
        phi = np.diff(phi)
        return phi
    phis = {
        c: dummy_phi(c, 30)
        for c in range(1, 4)
    }
    aids = ut.flatten(names)
    infr = ibeis.AnnotInference(ibs, aids, autoinit=True)
    infr.init_termination_criteria(phis)
    infr.init_refresh_criteria()

    # Partially review
    n1, n2, n3, n4 = names[0:4]
    for name in names[4:]:
        for a, b in ut.itertwo(name.aids):
            infr.add_feedback((a, b), POSTV)

    for name1, name2 in it.combinations(names[4:], 2):
        infr.add_feedback((name1.aids[0], name2.aids[0]), NEGTV)
    return infr


def demo2():
    """
    CommandLine:
        python -m ibeis.algo.graph.demo demo2 --viz
        python -m ibeis.algo.graph.demo demo2

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.algo.graph.demo import *  # NOQA
        >>> result = demo2()
        >>> print(result)
    """
    import plottool as pt

    from ibeis.scripts.thesis import TMP_RC
    import matplotlib as mpl
    mpl.rcParams.update(TMP_RC)

    # ---- Synthetic data params
    params = {
        'redun.pos': 2,
        'redun.neg': 2,
    }
    # oracle_accuracy = .98
    # oracle_accuracy = .90
    # oracle_accuracy = (.8, 1.0)
    oracle_accuracy = (.85, 1.0)
    # oracle_accuracy = 1.0

    # --- draw params

    VISUALIZE = ut.get_argflag('--viz')
    # QUIT_OR_EMEBED = 'embed'
    QUIT_OR_EMEBED = 'quit'
    TARGET_REVIEW = ut.get_argval('--target', type_=int, default=None)
    START = ut.get_argval('--start', type_=int, default=None)
    END = ut.get_argval('--end', type_=int, default=None)

    # ------------------

    # rng = np.random.RandomState(42)

    # infr = demodata_infr(num_pccs=4, size=3, size_std=1, p_incon=0)
    # infr = demodata_infr(num_pccs=6, size=7, size_std=1, p_incon=0)
    # infr = demodata_infr(num_pccs=3, size=5, size_std=.2, p_incon=0)
    infr = demodata_infr(pcc_sizes=[5, 2, 4])
    infr.verbose = 100
    # apply_dummy_viewpoints(infr)
    # infr.ensure_cliques()
    infr.ensure_cliques()
    infr.ensure_full()
    # infr.apply_edge_truth()
    # Dummy scoring

    infr.init_simulation(oracle_accuracy=oracle_accuracy, name='demo2')

    # infr_gt = infr.copy()

    dpath = ut.ensuredir(ut.truepath('~/Desktop/demo'))
    ut.remove_files_in_dir(dpath)

    fig_counter = it.count(0)

    def show_graph(infr, title, final=False, selected_edges=None):
        if not VISUALIZE:
            return
        # TODO: rich colored text?
        latest = '\n'.join(infr.latest_logs())
        showkw = dict(
            # fontsize=infr.graph.graph['fontsize'],
            # fontname=infr.graph.graph['fontname'],
            show_unreviewed_edges=True,
            show_inferred_same=False,
            show_inferred_diff=False,
            outof=(len(infr.aids)),
            # show_inferred_same=True,
            # show_inferred_diff=True,
            selected_edges=selected_edges,
            show_labels=True,
            simple_labels=True,
            # show_recent_review=not final,
            show_recent_review=False,
            # splines=infr.graph.graph['splines'],
            reposition=False,
            # with_colorbar=True
        )
        verbose = infr.verbose
        infr.verbose = 0
        infr_ = infr.copy()
        infr_ = infr
        infr_.verbose = verbose
        infr_.show(pickable=True, verbose=0, **showkw)
        infr.verbose = verbose
        # print('status ' + ut.repr4(infr_.status()))
        # infr.show(**showkw)
        ax = pt.gca()
        pt.set_title(title, fontsize=20)
        fig = pt.gcf()
        fontsize = 22
        if True:
            # postprocess xlabel
            lines = []
            for line in latest.split('\n'):
                if False and line.startswith('ORACLE ERROR'):
                    lines += ['ORACLE ERROR']
                else:
                    lines += [line]
            latest = '\n'.join(lines)
            if len(lines) > 10:
                fontsize = 16
            if len(lines) > 12:
                fontsize = 14
            if len(lines) > 14:
                fontsize = 12
            if len(lines) > 18:
                fontsize = 10

            if len(lines) > 23:
                fontsize = 8

        if True:
            pt.adjust_subplots(top=.95, left=0, right=1, bottom=.45,
                               fig=fig)
            ax.set_xlabel('\n' + latest)
            xlabel = ax.get_xaxis().get_label()
            xlabel.set_horizontalalignment('left')
            # xlabel.set_x(.025)
            xlabel.set_x(-.6)
            # xlabel.set_fontname('CMU Typewriter Text')
            xlabel.set_fontname('Inconsolata')
            xlabel.set_fontsize(fontsize)
        ax.set_aspect('equal')

        # ax.xaxis.label.set_color('red')

        from os.path import join

        fpath = join(dpath, 'demo_{:04d}.png'.format(next(fig_counter)))
        fig.savefig(fpath, dpi=300,
                    # transparent=True,
                    edgecolor='none')

        # pt.save_figure(dpath=dpath, dpi=300)
        infr.latest_logs()

    if VISUALIZE:
        infr.update_visual_attrs(groupby='name_label')
        infr.set_node_attrs('pin', 'true')
        print(ut.repr4(infr.graph.node[1]))

    if VISUALIZE:
        infr.latest_logs()
        # Pin Nodes into the target groundtruth position
        show_graph(infr, 'target-gt')

    print(ut.repr4(infr.status()))
    infr.clear_feedback()
    infr.clear_name_labels()
    infr.clear_edges()
    print(ut.repr4(infr.status()))
    infr.latest_logs()

    if VISUALIZE:
        infr.update_visual_attrs()

    infr.prioritize('prob_match')
    if VISUALIZE or TARGET_REVIEW is None or TARGET_REVIEW == 0:
        show_graph(infr, 'initial state')

    def on_new_candidate_edges(infr, edges):
        # hack updateing visual attrs as a callback
        infr.update_visual_attrs()

    infr.on_new_candidate_edges = on_new_candidate_edges

    infr.params.update(**params)
    infr.refresh_candidate_edges()

    VIZ_ALL = (VISUALIZE and TARGET_REVIEW is None and START is None)
    print('VIZ_ALL = %r' % (VIZ_ALL,))

    if VIZ_ALL or TARGET_REVIEW == 0:
        show_graph(infr, 'find-candidates')

    # _iter2 = enumerate(infr.generate_reviews(**params))
    # _iter2 = list(_iter2)
    # assert len(_iter2) > 0

    # prog = ut.ProgIter(_iter2, label='demo2', bs=False, adjust=False,
    #                    enabled=False)
    count = 1
    first = 1
    for edge, priority in infr._generate_reviews(data=True):
        msg = 'review #%d, priority=%.3f' % (count, priority)
        print('\n----------')
        infr.print('pop edge {} with priority={:.3f}'.format(edge, priority))
        # print('remaining_reviews = %r' % (infr.remaining_reviews()),)
        # Make the next review

        if START is not None:
            VIZ_ALL = count >= START

        if END is not None and count >= END:
            break

        infr.print(msg)
        if ut.allsame(infr.pos_graph.node_labels(*edge)) and first:
            # Have oracle make a mistake early
            feedback = infr.request_oracle_review(edge, accuracy=0)
            first -= 1
        else:
            feedback = infr.request_oracle_review(edge)

        AT_TARGET = TARGET_REVIEW is not None and count >= TARGET_REVIEW - 1

        SHOW_CANDIATE_POP = True
        if SHOW_CANDIATE_POP and (VIZ_ALL or AT_TARGET):
            # import utool
            # utool.embed()
            infr.print(ut.repr2(infr.task_probs['match_state'][edge], precision=4, si=True))
            infr.print('len(queue) = %r' % (len(infr.queue)))
            # Show edge selection
            infr.print('Oracle will predict: ' + feedback['evidence_decision'])
            show_graph(infr, 'pre' + msg, selected_edges=[edge])

        if count == TARGET_REVIEW:
            infr.EMBEDME = QUIT_OR_EMEBED == 'embed'
        infr.add_feedback(edge, **feedback)
        infr.print('len(queue) = %r' % (len(infr.queue)))
        # infr.apply_nondynamic_update()
        # Show the result
        if VIZ_ALL or AT_TARGET:
            show_graph(infr, msg)
            # import sys
            # sys.exit(1)
        if count == TARGET_REVIEW:
            break
        count += 1

    infr.print('status = ' + ut.repr4(infr.status(extended=False)))
    show_graph(infr, 'post-review (#reviews={})'.format(count), final=True)

    # ROUND 2 FIGHT
    # if TARGET_REVIEW is None and round2_params is not None:
    #     # HACK TO GET NEW THINGS IN QUEUE
    #     infr.params = round2_params

    #     _iter2 = enumerate(infr.generate_reviews(**params))
    #     prog = ut.ProgIter(_iter2, label='round2', bs=False, adjust=False,
    #                        enabled=False)
    #     for count, (aid1, aid2) in prog:
    #         msg = 'reviewII #%d' % (count)
    #         print('\n----------')
    #         print(msg)
    #         print('remaining_reviews = %r' % (infr.remaining_reviews()),)
    #         # Make the next review evidence_decision
    #         feedback = infr.request_oracle_review(edge)
    #         if count == TARGET_REVIEW:
    #             infr.EMBEDME = QUIT_OR_EMEBED == 'embed'
    #         infr.add_feedback(edge, **feedback)
    #         # Show the result
    #         if PRESHOW or TARGET_REVIEW is None or count >= TARGET_REVIEW - 1:
    #             show_graph(infr, msg)
    #         if count == TARGET_REVIEW:
    #             break

    #     show_graph(infr, 'post-re-review', final=True)

    if not getattr(infr, 'EMBEDME', False):
        if ut.get_computer_name().lower() in ['hyrule', 'ooo']:
            pt.all_figures_tile(monitor_num=0, percent_w=.5)
        else:
            pt.all_figures_tile()
        ut.show_if_requested()


valid_views = ['L', 'F', 'R', 'B']
adjacent_views = {
    v: [valid_views[(count + i) % len(valid_views)] for i in [-1, 0, 1]]
    for count, v in enumerate(valid_views)
}


def get_edge_truth(infr, n1, n2):
    nid1 = infr.graph.node[n1]['orig_name_label']
    nid2 = infr.graph.node[n2]['orig_name_label']
    try:
        view1 = infr.graph.node[n1]['viewpoint']
        view2 = infr.graph.node[n2]['viewpoint']
        comparable = view1 in adjacent_views[view2]
    except KeyError:
        comparable = True
        # raise
    same = nid1 == nid2

    if not comparable:
        return 2
    else:
        return int(same)


def apply_dummy_viewpoints(infr):
    transition_rate = .5
    transition_rate = 0
    valid_views = ['L', 'F', 'R', 'B']
    rng = np.random.RandomState(42)
    class MarkovView(object):
        def __init__(self):
            self.dir_ = +1
            self.state = 0

        def __call__(self):
            return self.next_state()

        def next_state(self):
            if self.dir_ == -1 and self.state <= 0:
                self.dir_ = +1
            if self.dir_ == +1 and self.state >= len(valid_views) - 1:
                self.dir_ = -1
            if rng.rand() < transition_rate:
                self.state += self.dir_
            return valid_views[self.state]
    mkv = MarkovView()
    nid_to_aids = ut.group_pairs([
        (n, d['name_label']) for n, d in infr.graph.nodes(data=True)])
    grouped_nodes = list(nid_to_aids.values())
    node_to_view = {node: mkv() for nodes in grouped_nodes for node in nodes}
    infr.set_node_attrs('viewpoint', node_to_view)


def make_demo_infr(ccs, edges=[], nodes=[], infer=True):
    import ibeis
    import networkx as nx

    if nx.__version__.startswith('1'):
        nx.add_path = nx.Graph.add_path

    G = ibeis.AnnotInference._graph_cls()
    G.add_nodes_from(nodes)
    for cc in ccs:
        if len(cc) == 1:
            G.add_nodes_from(cc)
        nx.add_path(G, cc, evidence_decision=POSTV, meta_decision=NULL)

    # for edge in edges:
    #     u, v, d = edge if len(edge) == 3 else tuple(edge) + ({},)

    G.add_edges_from(edges)
    infr = ibeis.AnnotInference.from_netx(G, infer=infer)
    infr.verbose = 3

    infr.relabel_using_reviews(rectify=False)

    infr.graph.graph['dark_background'] = False
    infr.graph.graph['ignore_labels'] = True
    infr.set_node_attrs('width', 40)
    infr.set_node_attrs('height', 40)
    # infr.set_node_attrs('fontsize', fontsize)
    # infr.set_node_attrs('fontname', fontname)
    infr.set_node_attrs('fixed_size', True)
    return infr


@profile
def demodata_infr(**kwargs):
    """
    kwargs = {}

    CommandLine:
        python -m ibeis.algo.graph.demo demodata_infr --show
        python -m ibeis.algo.graph.demo demodata_infr --num_pccs=25
        python -m ibeis.algo.graph.demo demodata_infr --profile --num_pccs=100

    Example:
        >>> from ibeis.algo.graph.demo import *  # NOQA
        >>> from ibeis.algo.graph import demo
        >>> import networkx as nx
        >>> kwargs = dict(num_pccs=6, p_incon=.5, size_std=2)
        >>> kwargs = ut.argparse_dict(kwargs)
        >>> infr = demo.demodata_infr(**kwargs)
        >>> pccs = list(infr.positive_components())
        >>> assert len(pccs) == kwargs['num_pccs']
        >>> nonfull_pccs = [cc for cc in pccs if len(cc) > 1 and nx.is_empty(nx.complement(infr.pos_graph.subgraph(cc)))]
        >>> expected_n_incon = len(nonfull_pccs) * kwargs['p_incon']
        >>> n_incon = len(list(infr.inconsistent_components()))
        >>> # TODO can test that we our sample num incon agrees with pop mean
        >>> #sample_mean = n_incon / len(nonfull_pccs)
        >>> #pop_mean = kwargs['p_incon']
        >>> print('status = ' + ut.repr4(infr.status(extended=True)))
        >>> ut.quit_if_noshow()
        >>> infr.show(pickable=True, groupby='name_label')
        >>> ut.show_if_requested()
    """
    import networkx as nx
    import vtool as vt
    from ibeis.algo.graph import nx_utils

    def kwalias(*args):
        params = args[0:-1]
        default = args[-1]
        for key in params:
            if key in kwargs:
                return kwargs[key]
        return default

    num_pccs = kwalias('num_pccs', 16)
    size_mean = kwalias('pcc_size_mean', 'pcc_size', 'size', 5)
    size_std = kwalias('pcc_size_std', 'size_std', 0)
    # p_pcc_incon = kwargs.get('p_incon', .1)
    p_pcc_incon = kwargs.get('p_incon', 0)
    p_pcc_incomp = kwargs.get('p_incomp', 0)
    pcc_sizes = kwalias('pcc_sizes', None)

    # number of maximum inconsistent edges per pcc
    max_n_incon = kwargs.get('n_incon', 3)

    rng = np.random.RandomState(0)
    counter = 1
    new_ccs = []

    if pcc_sizes is None:
        pcc_sizes = [int(randn(size_mean, size_std, rng=rng, a_min=1))
                     for _ in range(num_pccs)]
    else:
        num_pccs = len(pcc_sizes)

    pcc_iter = list(enumerate(pcc_sizes))
    pcc_iter = ut.ProgIter(pcc_iter, enabled=num_pccs > 20,
                           label='make pos-demo')
    for i, size in pcc_iter:
        p = .1
        want_connectivity = rng.choice([1, 2, 3])
        want_connectivity = min(size - 1, want_connectivity)

        # Create basic graph of positive edges with desired connectivity
        g = nx_utils.random_k_edge_connected_graph(
            size, k=want_connectivity, p=p, rng=rng)
        new_nodes = np.array(list(g.nodes()))
        new_edges_ = np.array(list(g.edges()))
        new_edges_ += counter
        new_nodes += counter
        counter = new_nodes.max() + 1
        new_edges = [
            (int(min(u, v)), int(max(u, v)), {'evidence_decision': POSTV, 'truth': POSTV})
            for u, v in new_edges_
        ]
        new_g = nx.Graph(new_edges)
        new_g.add_nodes_from(new_nodes)
        assert nx.is_connected(new_g)

        # The probability any edge is inconsistent is `p_incon`
        # This is 1 - P(all edges consistent)
        # which means p(edge is consistent) = (1 - p_incon) / N
        complement_edges = ut.estarmap(nx_utils.e_,
                                       nx_utils.complement_edges(new_g))
        if len(complement_edges) > 0:
            # compute probability that any particular edge is inconsistent
            # to achieve probability the PCC is inconsistent
            p_edge_inconn = 1 - (1 - p_pcc_incon) ** (1 / len(complement_edges))
            p_edge_unrev = .1
            p_edge_notcomp = 1 - (1 - p_pcc_incomp) ** (1 / len(complement_edges))
            probs = np.array([p_edge_inconn, p_edge_unrev, p_edge_notcomp])
            # if the total probability is greater than 1 the parameters
            # are invalid, so we renormalize to "fix" it.
            # if probs.sum() > 1:
            #     warnings.warn('probabilities sum to more than 1')
            #     probs = probs / probs.sum()
            pcumsum = probs.cumsum()
            # Determine which mutually exclusive state each complement edge is in
            # print('pcumsum = %r' % (pcumsum,))
            states = np.searchsorted(pcumsum, rng.rand(len(complement_edges)))

            incon_idxs = np.where(states == 0)[0]
            if len(incon_idxs) > max_n_incon:
                print('max_n_incon = %r' % (max_n_incon,))
                chosen = rng.choice(incon_idxs, max_n_incon, replace=False)
                states[np.setdiff1d(incon_idxs, chosen)] = len(probs)

            grouped_edges = ut.group_items(complement_edges, states)
            for state, edges in grouped_edges.items():
                truth = POSTV
                if state == 0:
                    # Add in inconsistent edges
                    evidence_decision = NEGTV
                    # TODO: truth could be INCMP or POSTV
                    # new_edges.append((u, v, {'evidence_decision': NEGTV}))
                elif state == 1:
                    evidence_decision = UNREV
                    # TODO: truth could be INCMP or POSTV
                    # new_edges.append((u, v, {'evidence_decision': UNREV}))
                elif state == 2:
                    evidence_decision = INCMP
                    truth = INCMP
                else:
                    continue
                # Add in candidate edges
                attrs = {'evidence_decision': evidence_decision, 'truth': truth}
                for (u, v) in edges:
                    new_edges.append((u, v, attrs))
        new_ccs.append((new_nodes, new_edges))

    pos_g = nx.Graph(ut.flatten(ut.take_column(new_ccs, 1)))
    pos_g.add_nodes_from(ut.flatten(ut.take_column(new_ccs, 0)))
    assert num_pccs == len(list(nx.connected_components(pos_g)))

    # Add edges between the PCCS
    neg_edges = []

    if not kwalias('ignore_pair', False):
        print('making pairs')

        pair_attrs_lookup = {
            0: {'evidence_decision': NEGTV, 'truth': NEGTV},
            1: {'evidence_decision': INCMP, 'truth': INCMP},
            2: {'evidence_decision': UNREV, 'truth': NEGTV},  # could be incomp or neg
        }

        # These are the probabilities that one edge has this state
        p_pair_neg = kwalias('p_pair_neg', .4)
        p_pair_incmp = kwalias('p_pair_incmp', .2)
        p_pair_unrev = kwalias('p_pair_unrev', 0)

        # p_pair_neg = 1
        cc_combos = ((itempair[0][0], itempair[1][0])
                     for itempair in it.combinations(new_ccs, 2))
        valid_cc_combos = [
            (cc1, cc2)
            for cc1, cc2 in cc_combos if len(cc1) and len(cc2)
        ]
        for cc1, cc2 in ut.ProgIter(valid_cc_combos, label='make neg-demo'):
            possible_edges = ut.estarmap(nx_utils.e_, it.product(cc1, cc2))
            # probability that any edge between these PCCs is negative
            n_edges = len(possible_edges)
            p_edge_neg   = 1 - (1 - p_pair_neg)   ** (1 / n_edges)
            p_edge_incmp = 1 - (1 - p_pair_incmp) ** (1 / n_edges)
            p_edge_unrev = 1 - (1 - p_pair_unrev) ** (1 / n_edges)

            # Create event space with sizes proportional to probabilities
            pcumsum = np.cumsum([p_edge_neg, p_edge_incmp, p_edge_unrev])
            # Roll dice for each of the edge to see which state it lands on
            possible_pstate = rng.rand(len(possible_edges))
            states = np.searchsorted(pcumsum, possible_pstate)

            flags = states < len(pcumsum)
            stateful_states = states.compress(flags)
            stateful_edges = ut.compress(possible_edges, flags)

            unique_states, groupxs_list = vt.group_indices(stateful_states)
            for state, groupxs in zip(unique_states, groupxs_list):
                # print('state = %r' % (state,))
                # Add in candidate edges
                edges = ut.take(stateful_edges, groupxs)
                attrs = pair_attrs_lookup[state]
                for (u, v) in edges:
                    neg_edges.append((u, v, attrs))
        print('Made {} neg_edges between PCCS'.format(len(neg_edges)))
    else:
        print('ignoring pairs')

    edges = ut.flatten(ut.take_column(new_ccs, 1)) + neg_edges
    edges = [(int(u), int(v), d) for u, v, d in edges]
    nodes = ut.flatten(ut.take_column(new_ccs, 0))
    infr = make_demo_infr([], edges, nodes=nodes,
                          infer=kwargs.get('infer', True))

    # fontname = 'Ubuntu'
    fontsize = 12
    fontname = 'sans'
    splines = 'spline'
    # splines = 'ortho'
    # splines = 'line'
    infr.set_node_attrs('shape', 'circle')
    infr.graph.graph['ignore_labels'] = True
    infr.graph.graph['dark_background'] = False
    infr.graph.graph['fontname'] = fontname
    infr.graph.graph['fontsize'] = fontsize
    infr.graph.graph['splines'] = splines
    infr.set_node_attrs('width', 29)
    infr.set_node_attrs('height', 29)
    infr.set_node_attrs('fontsize', fontsize)
    infr.set_node_attrs('fontname', fontname)
    infr.set_node_attrs('fixed_size', True)

    # Set synthetic ground-truth attributes for testing
    # infr.apply_edge_truth()
    infr.edge_truth = infr.get_edge_attrs('truth')
    # Make synthetic matcher
    infr.dummy_matcher = DummyMatcher(infr)
    infr.demokw = kwargs
    return infr


def randn(mean=0, std=1, shape=[], a_max=None, a_min=None, rng=None):
    a = (rng.randn(*shape) * std) + mean
    if a_max is not None or a_min is not None:
        a = np.clip(a, a_min, a_max)
    return a


class DummyMatcher(object):
    """
    generates dummy scores between edges (not necesarilly in the graph)

    CommandLine:
        python -m ibeis.algo.graph.demo DummyMatcher:1

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.algo.graph.demo import *  # NOQA
        >>> from ibeis.algo.graph import demo
        >>> import networkx as nx
        >>> kwargs = dict(num_pccs=6, p_incon=.5, size_std=2)
        >>> infr = demo.demodata_infr(**kwargs)
        >>> infr.dummy_matcher.predict_edges([(1, 2)])
        >>> infr.dummy_matcher.predict_edges([(1, 21)])
        >>> assert len(infr.dummy_matcher.infr.task_probs['match_state']) == 2
    """
    def __init__(matcher, infr):
        matcher.rng = np.random.RandomState(4033913)
        matcher.dummy_params = {
            NEGTV: {'mean': .2, 'std': .25},
            POSTV: {'mean': .85, 'std': .2},
            INCMP: {'mean': .15, 'std': .1},
        }
        matcher.score_dist = randn

        matcher.infr = infr
        matcher.orig_nodes = set(infr.aids)
        matcher.orig_labels = infr.get_node_attrs('orig_name_label')
        matcher.orig_groups = ut.invert_dict(matcher.orig_labels, False)
        matcher.orig_groups = ut.map_vals(set, matcher.orig_groups)

    def show_score_probs(matcher):
        """
        CommandLine:
            python -m ibeis.algo.graph.demo DummyMatcher.show_score_probs --show

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.algo.graph.demo import *  # NOQA
            >>> import ibeis
            >>> infr = ibeis.AnnotInference(None)
            >>> matcher = DummyMatcher(infr)
            >>> matcher.show_score_probs()
            >>> ut.show_if_requested()
        """
        import plottool as pt
        dist = matcher.score_dist
        n = 100000
        for key in matcher.dummy_params.keys():
            probs = dist(shape=[n], rng=matcher.rng, a_max=1, a_min=0,
                          **matcher.dummy_params[key])
            color = matcher.infr._get_truth_colors()[key]
            pt.plt.hist(probs, bins=100, label=key, alpha=.8, color=color)
        pt.legend()

    def dummy_ranker(matcher, u, K=10):
        """
        simulates the ranking algorithm. Order is defined using the dummy vsone
        scores, but tests are only applied to randomly selected gt and gf
        pairs. So, you usually will get a gt result, but you might not if all
        the scores are bad.
        """
        infr = matcher.infr

        nid = matcher.orig_labels[u]
        others = matcher.orig_groups[nid]
        others_gt = sorted(others - {u})
        others_gf = sorted(matcher.orig_nodes - others)

        # rng = np.random.RandomState(u + 4110499444 + len(others))
        rng = matcher.rng

        vs_list = []
        k_gt = min(len(others_gt), max(1, K // 2))
        k_gf = min(len(others_gf), max(1, K * 4))
        if k_gt > 0:
            gt = rng.choice(others_gt, k_gt, replace=False)
            vs_list.append(gt)
        if k_gf > 0:
            gf = rng.choice(others_gf, k_gf, replace=False)
            vs_list.append(gf)

        u_edges = [infr.e_(u, v) for v in it.chain.from_iterable(vs_list)]
        u_probs = np.array(infr.dummy_matcher.predict_edges(u_edges))
        # infr.set_edge_attrs('prob_match', ut.dzip(u_edges, u_probs))

        # Need to determenistically sort here
        # sortx = np.argsort(u_probs)[::-1][0:K]

        sortx = np.argsort(u_probs)[::-1][0:K]
        ranked_edges = ut.take(u_edges, sortx)
        # assert len(ranked_edges) == K
        return ranked_edges

    def find_candidate_edges(matcher, K=10):
        """
        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.algo.graph.demo import *  # NOQA
            >>> from ibeis.algo.graph import demo
            >>> import networkx as nx
            >>> kwargs = dict(num_pccs=40, size=2)
            >>> infr = demo.demodata_infr(**kwargs)
            >>> edges = list(infr.dummy_matcher.find_candidate_edges(K=100))
            >>> scores = np.array(infr.dummy_matcher.predict_edges(edges))
        """
        new_edges = []
        nodes = list(matcher.infr.graph.nodes())
        for u in nodes:
            new_edges.extend(matcher.dummy_ranker(u, K=K))
        # print('new_edges = %r' % (ut.hash_data(new_edges),))
        new_edges = set(new_edges)
        return new_edges

    def _get_truth(matcher, edge):
        infr = matcher.infr
        if edge in infr.edge_truth:
            return infr.edge_truth[edge]
        nid1 = infr.graph.node[edge[0]]['orig_name_label']
        nid2 = infr.graph.node[edge[1]]['orig_name_label']
        return POSTV if nid1 == nid2 else NEGTV

    def predict_edges(matcher, edges):
        """
        CommandLine:
            python -m ibeis.algo.graph.demo DummyMatcher.predict_edges

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.algo.graph.demo import *  # NOQA
            >>> from ibeis.algo.graph import demo
            >>> import networkx as nx
            >>> kwargs = dict(num_pccs=40, size=2)
            >>> infr = demo.demodata_infr(**kwargs)
            >>> edges = list(infr.graph.edges())
            >>> scores = np.array(infr.dummy_matcher.predict_edges(edges))
            >>> #print('scores = %r' % (scores,))
            >>> #hashid = ut.hash_data(scores)
            >>> #print('hashid = %r' % (hashid,))
            >>> #assert hashid == 'cdlkytilfeqgmtsihvhqwffmhczqmpil'
        """
        infr = matcher.infr
        edges = list(it.starmap(matcher.infr.e_, edges))
        prob_cache = infr.task_probs['match_state']
        is_miss = np.array([e not in prob_cache for e in edges])
        # is_hit = ~is_miss
        if np.any(is_miss):
            miss_edges = ut.compress(edges, is_miss)
            miss_truths = [matcher._get_truth(edge) for edge in miss_edges]
            grouped_edges = ut.group_items(miss_edges, miss_truths,
                                           sorted_=False)
            # Need to make this determenistic too
            states = [POSTV, NEGTV, INCMP]
            for key in sorted(grouped_edges.keys()):
                group = grouped_edges[key]
                probs0 = randn(shape=[len(group)], rng=matcher.rng, a_max=1, a_min=0,
                               **matcher.dummy_params[key])
                # Just randomly assign other probs
                probs1 = matcher.rng.rand(len(group)) * (1 - probs0)
                probs2 = 1 - (probs0 + probs1)
                for edge, probs in zip(group, zip(probs0, probs1, probs2)):
                    prob_cache[edge] = ut.dzip(states, probs)
        pos_scores = ut.take_column(ut.take(prob_cache, edges), POSTV)
        return pos_scores

if __name__ == '__main__':
    r"""
    CommandLine:
        ibeis make_qt_graph_interface --show --aids=1,2,3,4,5,6,7 --graph
        python -m ibeis.algo.graph.demo demo2
        python -m ibeis.algo.graph.demo
        python -m ibeis.algo.graph.demo --allexamples
        python -m ibeis.algo.graph.demo --allexamples --show
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
