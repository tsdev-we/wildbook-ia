"""
TODO: Module Licence and docstring

functions in the IBEISController have been split up into several submodules.
"""
# TODO: rename annotation annotations
# TODO: make all names consistent
from __future__ import absolute_import, division, print_function
# Python
import six
import atexit
import requests
import weakref
from six.moves import zip, range
from os.path import join, split
# UTool
import utool as ut  # NOQA
# IBEIS
import ibeis  # NOQA
from ibeis import constants as const
from ibeis import params
from ibeis.control.accessor_decors import (default_decorator, )
# Import modules which define injectable functions
# Older manual ibeiscontrol functions
from ibeis import ibsfuncs
#from ibeis.control import controller_inject


# Shiny new way to inject external functions
autogenmodname_list = [
    '_autogen_featweight_funcs',
    #'_autogen_annot_funcs',
    'manual_ibeiscontrol_funcs',
    'manual_meta_funcs',
    'manual_lbltype_funcs',
    'manual_lblannot_funcs',
    'manual_lblimage_funcs',
    'manual_image_funcs',
    'manual_annot_funcs',
    'manual_name_species_funcs',
    'manual_dependant_funcs',
]

INJECTED_MODULES = []

for modname in autogenmodname_list:
    exec('from ibeis.control import ' + modname, globals(), locals())
    module = eval(modname)
    INJECTED_MODULES.append(module)
# Inject utool functions
(print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[ibs]')


__ALL_CONTROLLERS__ = []  # Global variable containing all created controllers
__IBEIS_CONTROLLER_CACHE__ = {}


def request_IBEISController(dbdir=None, ensure=True, wbaddr=None, verbose=True, use_cache=True):
    r"""
    Alternative to directory instantiating a new controller object. Might
    return a memory cached object

    Args:
        dbdir     (str):
        ensure    (bool):
        wbaddr    (None):
        verbose   (bool):
        use_cache (bool):

    Returns:
        IBEISController: ibs

    CommandLine:
        python -m ibeis.control.IBEISControl --test-request_IBEISController

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.IBEISControl import *  # NOQA
        >>> dbdir = 'testdb1'
        >>> ensure = True
        >>> wbaddr = None
        >>> verbose = True
        >>> use_cache = False
        >>> ibs = request_IBEISController(dbdir, ensure, wbaddr, verbose, use_cache)
        >>> result = str(ibs)
        >>> print(result)
    """
    # TODO: change name from new to request
    global __IBEIS_CONTROLLER_CACHE__
    if use_cache and dbdir in __IBEIS_CONTROLLER_CACHE__:
        if verbose:
            print('[request_IBEISController] returning cached controller')
        ibs = __IBEIS_CONTROLLER_CACHE__[dbdir]
    else:
        ibs = IBEISController(dbdir=dbdir, ensure=ensure, wbaddr=wbaddr, verbose=verbose)
        __IBEIS_CONTROLLER_CACHE__[dbdir] = ibs
    return ibs


@atexit.register
def __cleanup():
    """ prevents flann errors (not for cleaning up individual objects) """
    global __ALL_CONTROLLERS__
    global __IBEIS_CONTROLLER_CACHE__
    try:
        del __ALL_CONTROLLERS__
        del __IBEIS_CONTROLLER_CACHE__
    except NameError:
        print('cannot cleanup IBEISController')
        pass


#
#
#-----------------
# IBEIS CONTROLLER
#-----------------

@six.add_metaclass(ut.ReloadingMetaclass)
class IBEISController(object):
    """
    IBEISController docstring

    chip  - cropped region of interest in an image, maps to one animal
    cid   - chip unique id
    gid   - image unique id (could just be the relative file path)
    name  - name unique id
    eid   - encounter unique id
    aid   - region of interest unique id
    annotation   - region of interest for a chip
    theta - angle of rotation for a chip
    """

    #
    #
    #-------------------------------
    # --- CONSTRUCTOR / PRIVATES ---
    #-------------------------------

    def __init__(ibs, dbdir=None, ensure=True, wbaddr=None, verbose=True):
        """ Creates a new IBEIS Controller associated with one database """
        if verbose and ut.VERBOSE:
            print('[ibs.__init__] new IBEISController')
        # an dict to hack in temporary state
        ibs.temporary_state = {}
        ibs.allow_override = 'override+warn'
        # observer_weakref_list keeps track of the guibacks connected to this controller
        ibs.observer_weakref_list = []
        # not completely working decorator cache
        #ibs.table_cache = init_tablecache()
        ibs._initialize_self()
        ibs._init_dirs(dbdir=dbdir, ensure=ensure)
        # _init_wb will do nothing if no wildbook address is specified
        ibs._init_wb(wbaddr)
        ibs._init_sql()
        ibs._init_config()

    def _initialize_self(ibs):
        """
        For utools auto reload
        Called after reload
        Injects code from development modules into the controller
        """
        if ut.VERBOSE:
            print('[ibs] _initialize_self()')

        for module in INJECTED_MODULES:
            ut.inject_instance(
                ibs, classtype=module.CLASS_INJECT_KEY,
                allow_override=ibs.allow_override, strict=False)
        ut.inject_instance(ibs, classtype=ibsfuncs.CLASS_INJECT_KEY,
                           allow_override=ibs.allow_override, strict=True)
        assert hasattr(ibs, 'get_database_species'), 'issue with ibsfuncs'

        #ut.inject_instance(ibs, classtype=('IBEISController', 'autogen_featweight'),
        #                   allow_override=ibs.allow_override, strict=False)
        #ut.inject_instance(ibs, classtype=('IBEISController', 'manual'),
        #                   allow_override=ibs.allow_override, strict=False)
        ibs.register_controller()

    def _on_reload(ibs):
        """
        For utools auto reload.
        Called before reload
        """
        # Only warn on first load. Overrideing while reloading is ok
        ibs.allow_override = True
        ibs.unregister_controller()
        # Reload dependent modules
        for module in INJECTED_MODULES:
            module.rrr()
        ibsfuncs.rrr()
        pass

    # We should probably not implement __del__
    # see: https://docs.python.org/2/reference/datamodel.html#object.__del__
    #def __del__(ibs):
    #    ibs.cleanup()

    # ------------
    # SELF REGISTRATION
    # ------------

    def register_controller(ibs):
        """ registers controller with global list """
        ibs_weakref = weakref.ref(ibs)
        __ALL_CONTROLLERS__.append(ibs_weakref)

    def unregister_controller(ibs):
        ibs_weakref = weakref.ref(ibs)
        try:
            __ALL_CONTROLLERS__.remove(ibs_weakref)
            pass
        except ValueError:
            pass

    # ------------
    # OBSERVER REGISTRATION
    # ------------

    def cleanup(ibs):
        """ call on del? """
        print('[ibs.cleanup] Observers (if any) notified [controller killed]')
        for observer_weakref in ibs.observer_weakref_list:
            observer_weakref().notify_controller_killed()

    @default_decorator
    def register_observer(ibs, observer):
        print('[register_observer] Observer registered: %r' % observer)
        observer_weakref = weakref.ref(observer)
        ibs.observer_weakref_list.append(observer_weakref)

    @default_decorator
    def remove_observer(ibs, observer):
        print('[remove_observer] Observer removed: %r' % observer)
        ibs.observer_weakref_list.remove(observer)

    @default_decorator
    def notify_observers(ibs):
        print('[notify_observers] Observers (if any) notified')
        for observer_weakref in ibs.observer_weakref_list:
            observer_weakref().notify()

    # ------------

    def _init_rowid_constants(ibs):
        ibs.UNKNOWN_LBLANNOT_ROWID = 0  # ADD TO CONSTANTS
        ibs.UNKNOWN_NAME_ROWID     = ibs.UNKNOWN_LBLANNOT_ROWID  # ADD TO CONSTANTS
        ibs.UNKNOWN_SPECIES_ROWID  = ibs.UNKNOWN_LBLANNOT_ROWID  # ADD TO CONSTANTS
        ibs.MANUAL_CONFIG_SUFFIX = 'MANUAL_CONFIG'
        ibs.MANUAL_CONFIGID = ibs.add_config(ibs.MANUAL_CONFIG_SUFFIX)
        # duct_tape.fix_compname_configs(ibs)
        # duct_tape.remove_database_slag(ibs)
        # duct_tape.fix_nulled_viewpoints(ibs)
        lbltype_names    = const.KEY_DEFAULTS.keys()
        lbltype_defaults = const.KEY_DEFAULTS.values()
        lbltype_ids = ibs.add_lbltype(lbltype_names, lbltype_defaults)
        ibs.lbltype_ids = dict(zip(lbltype_names, lbltype_ids))

    @default_decorator
    def _init_sql(ibs):
        """ Load or create sql database """
        from ibeis.dev import duct_tape  # NOQA
        ibs._init_sqldb()
        ibs._init_sqldbcache()
        # ibs.db.dump_schema()
        # ibs.db.dump()
        ibs._init_rowid_constants()

    @ut.indent_func
    def _init_sqldb(ibs):
        from ibeis.control import _sql_helpers
        from ibeis.control import SQLDatabaseControl as sqldbc
        from ibeis.control import DB_SCHEMA
        # Before load, ensure database has been backed up for the day
        _sql_helpers.ensure_daily_database_backup(ibs.get_ibsdir(), ibs.sqldb_fname, ibs.backupdir)
        # IBEIS SQL State Database
        #ibs.db_version_expected = '1.1.1'
        ibs.db_version_expected = '1.2.0'

        # TODO: add this functionality to SQLController
        #testing_newschmea = ut.is_developer() and ibs.get_dbname() in ['PZ_MTEST', 'testdb1']
        #if testing_newschmea:
        #    # Set to true until the schema module is good then continue tests with this set to false
        #    testing_force_fresh = True or ut.get_argflag('--force-fresh')
        #    # Work on a fresh schema copy when developing
        #    dev_sqldb_fname = ut.augpath(ibs.sqldb_fname, '_develop_schema')
        #    sqldb_fpath = join(ibs.get_ibsdir(), ibs.sqldb_fname)
        #    dev_sqldb_fpath = join(ibs.get_ibsdir(), dev_sqldb_fname)
        #    ut.copy(sqldb_fpath, dev_sqldb_fpath, overwrite=testing_force_fresh)
        #    ibs.db_version_expected = '1.2.0'
        ibs.db = sqldbc.SQLDatabaseController(ibs.get_ibsdir(), ibs.sqldb_fname,
                                              text_factory=const.__STR__,
                                              inmemory=False)
        # Ensure correct schema versions
        _sql_helpers.ensure_correct_version(
            ibs,
            ibs.db,
            ibs.db_version_expected,
            DB_SCHEMA,
            autogenerate=params.args.dump_autogen_schema
        )

    @ut.indent_func
    def _init_sqldbcache(ibs):
        """ Need to reinit this sometimes if cache is ever deleted """
        from ibeis.control import _sql_helpers
        from ibeis.control import SQLDatabaseControl as sqldbc
        from ibeis.control import DBCACHE_SCHEMA
        # IBEIS SQL Features & Chips database
        ibs.dbcache_version_expected = '1.0.3'
        ibs.dbcache = sqldbc.SQLDatabaseController(
            ibs.get_cachedir(), ibs.sqldbcache_fname, text_factory=const.__STR__)
        _sql_helpers.ensure_correct_version(
            ibs,
            ibs.dbcache,
            ibs.dbcache_version_expected,
            DBCACHE_SCHEMA,
            dobackup=False,  # Everything in dbcache can be regenerated.
            autogenerate=params.args.dump_autogen_schema
        )

    def _close_sqldbcache(ibs):
        ibs.dbcache.close()
        ibs.dbcache = None

    @default_decorator
    def clone_handle(ibs, **kwargs):
        ibs2 = IBEISController(dbdir=ibs.get_dbdir(), ensure=False)
        if len(kwargs) > 0:
            ibs2.update_query_cfg(**kwargs)
        #if ibs.qreq is not None:
        #    ibs2._prep_qreq(ibs.qreq.qaids, ibs.qreq.daids)
        return ibs2

    @default_decorator
    def backup_database(ibs):
        from ibeis.control import _sql_helpers
        _sql_helpers.database_backup(ibs.get_ibsdir(), ibs.sqldb_fname, ibs.backupdir)

    @default_decorator
    def _init_wb(ibs, wbaddr):
        if wbaddr is None:
            return
        #TODO: Clean this up to use like ut and such
        try:
            requests.get(wbaddr)
        except requests.MissingSchema as msa:
            print('[ibs._init_wb] Invalid URL: %r' % wbaddr)
            raise msa
        except requests.ConnectionError as coe:
            print('[ibs._init_wb] Could not connect to Wildbook server at %r' % wbaddr)
            raise coe
        ibs.wbaddr = wbaddr

    @default_decorator
    def _init_dirs(ibs, dbdir=None, dbname='testdb_1', workdir='~/ibeis_workdir', ensure=True):
        """
        Define ibs directories
        """
        PATH_NAMES = const.PATH_NAMES
        REL_PATHS = const.REL_PATHS

        if ensure and not ut.QUIET:
            print('[ibs._init_dirs] ibs.dbdir = %r' % dbdir)
        if dbdir is not None:
            if not ut.QUIET:
                print(dbdir)
            workdir, dbname = split(dbdir)
        ibs.workdir  = ut.truepath(workdir)
        ibs.dbname = dbname
        ibs.sqldb_fname = PATH_NAMES.sqldb
        ibs.sqldbcache_fname = PATH_NAMES.sqldbcache

        # Make sure you are not nesting databases
        assert PATH_NAMES._ibsdb != ut.dirsplit(ibs.workdir), \
            'cannot work in _ibsdb internals'
        assert PATH_NAMES._ibsdb != dbname,\
            'cannot create db in _ibsdb internals'
        ibs.dbdir    = join(ibs.workdir, ibs.dbname)
        # All internal paths live in <dbdir>/_ibsdb
        # TODO: constantify these
        # so non controller objects (like in score normalization) have access to
        # these
        ibs._ibsdb      = join(ibs.dbdir, REL_PATHS._ibsdb)
        ibs.trashdir    = join(ibs.dbdir, REL_PATHS.trashdir)
        ibs.cachedir    = join(ibs.dbdir, REL_PATHS.cache)
        ibs.backupdir   = join(ibs.dbdir, REL_PATHS.backups)
        ibs.chipdir     = join(ibs.dbdir, REL_PATHS.chips)
        ibs.imgdir      = join(ibs.dbdir, REL_PATHS.images)
        # All computed dirs live in <dbdir>/_ibsdb/_ibeis_cache
        ibs.thumb_dpath = join(ibs.dbdir, REL_PATHS.thumbs)
        ibs.flanndir    = join(ibs.dbdir, REL_PATHS.flann)
        ibs.qresdir     = join(ibs.dbdir, REL_PATHS.qres)
        ibs.bigcachedir = join(ibs.dbdir, REL_PATHS.bigcache)
        if ensure:
            ibs.ensure_directories()
        assert dbdir is not None, 'must specify database directory'

    def ensure_directories(ibs):
        """
        Makes sure the core directores for the controller exist
        """
        _verbose = ut.VERBOSE
        ut.ensuredir(ibs._ibsdb)
        ut.ensuredir(ibs.cachedir,    verbose=_verbose)
        ut.ensuredir(ibs.backupdir,   verbose=_verbose)
        ut.ensuredir(ibs.workdir,     verbose=_verbose)
        ut.ensuredir(ibs.imgdir,      verbose=_verbose)
        ut.ensuredir(ibs.chipdir,     verbose=_verbose)
        ut.ensuredir(ibs.flanndir,    verbose=_verbose)
        ut.ensuredir(ibs.qresdir,     verbose=_verbose)
        ut.ensuredir(ibs.bigcachedir, verbose=_verbose)
        ut.ensuredir(ibs.thumb_dpath, verbose=_verbose)

    #
    #
    #--------------
    # --- DIRS ----
    #--------------

    def get_dbname(ibs):
        """
        Returns:
            list_ (list): database name """
        return ibs.dbname

    def get_dbdir(ibs):
        """
        Returns:
            list_ (list): database dir with ibs internal directory """
        #return join(ibs.workdir, ibs.dbname)
        return ibs.dbdir

    def get_trashdir(ibs):
        return ibs.trashdir

    def get_ibsdir(ibs):
        """
        Returns:
            list_ (list): ibs internal directory """
        return ibs._ibsdb

    def get_fig_dir(ibs):
        """
        Returns:
            list_ (list): ibs internal directory """
        return join(ibs._ibsdb, 'figures')

    def get_imgdir(ibs):
        """
        Returns:
            list_ (list): ibs internal directory """
        return ibs.imgdir

    def get_thumbdir(ibs):
        """
        Returns:
            list_ (list): database directory where thumbnails are cached """
        return ibs.thumb_dpath

    def get_workdir(ibs):
        """
        Returns:
            list_ (list): directory where databases are saved to """
        return ibs.workdir

    def get_cachedir(ibs):
        """
        Returns:
            list_ (list): database directory of all cached files """
        return ibs.cachedir

    def get_ibeis_resource_dir(ibs):
        from ibeis.dev import sysres
        return sysres.get_ibeis_resource_dir()

    def get_scorenorm_cachedir(ibs, ensure=True):
        """

        Args:
            species_text (str):
            ensure       (bool):

        Returns:
            str: species_cachedir

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.control.IBEISControl import *  # NOQA
            >>> import ibeis
            >>> ibs = ibeis.opendb('testdb1')
            >>> scorenorm_cachedir = ibs.get_scorenorm_cachedir()
            >>> resourcedir = ibs.get_ibeis_resource_dir()
            >>> result = ut.relpath_unix(scorenorm_cachedir, resourcedir)
            >>> print(result)
            score_normalizers
        """
        scorenorm_cachedir = join(ibs.get_ibeis_resource_dir(), 'score_normalizers')
        if ensure:
            ut.ensurepath(scorenorm_cachedir)
        return scorenorm_cachedir

    def get_species_scorenorm_cachedir(ibs, species_text, ensure=True):
        """

        Args:
            species_text (str):
            ensure       (bool):

        Returns:
            str: species_cachedir

        CommandLine:
            python -m ibeis.control.IBEISControl --test-get_species_scorenorm_cachedir

        Example:
            >>> # ENABLE_DOCTEST
            >>> from ibeis.control.IBEISControl import *  # NOQA
            >>> import ibeis
            >>> ibs = ibeis.opendb('testdb1')
            >>> species_text = ibeis.const.Species.ZEB_GREVY
            >>> ensure = True
            >>> species_cachedir = ibs.get_species_scorenorm_cachedir(species_text, ensure)
            >>> species_cachedir = ibs.get_species_scorenorm_cachedir(ibeis.const.Species.ZEB_GREVY, ensure)
            >>> resourcedir = ibs.get_ibeis_resource_dir()
            >>> result = ut.relpath_unix(species_cachedir, resourcedir)
            >>> print(result)
            score_normalizers/zebra_grevys

        """
        scorenorm_cachedir = ibs.get_scorenorm_cachedir()
        species_cachedir = join(scorenorm_cachedir, species_text)
        if ensure:
            ut.ensuredir(species_cachedir)
        return species_cachedir

    def get_detect_modeldir(ibs):
        from ibeis.dev import sysres
        return join(sysres.get_ibeis_resource_dir(), 'detectmodels')

    def get_detectimg_cachedir(ibs):
        """
        Returns:
            list_ (list): database directory of image resized for detections """
        return join(ibs.cachedir, const.PATH_NAMES.detectimg)

    def get_flann_cachedir(ibs):
        """
        Returns:
            list_ (list): database directory where the FLANN KD-Tree is stored """
        return ibs.flanndir

    def get_qres_cachedir(ibs):
        """
        Returns:
            list_ (list): database directory where query results are stored """
        return ibs.qresdir

    def get_big_cachedir(ibs):
        """
        Returns:
            list_ (list): database directory where aggregate results are stored """
        return ibs.bigcachedir

    #
    #
    #----------------
    # --- Configs ---
    #----------------

    @default_decorator
    def export_to_wildbook(ibs):
        """ Exports identified chips to wildbook """
        import ibeis.dbio.export_wb as wb
        print('[ibs] exporting to wildbook')
        eid_list = ibs.get_valid_eids()
        addr = "http://127.0.0.1:8080/wildbook-4.1.0-RELEASE"
        #addr = "http://tomcat:tomcat123@127.0.0.1:8080/wildbook-5.0.0-EXPERIMENTAL"
        ibs._init_wb(addr)
        wb.export_ibeis_to_wildbook(ibs, eid_list)
        #raise NotImplementedError()
        # compute encounters
        # get encounters by id
        # get ANNOTATIONs by encounter id
        # submit requests to wildbook
        return None

    #
    #
    #------------------
    # --- DETECTION ---
    #------------------

    @default_decorator
    def detect_existence(ibs, gid_list, **kwargs):
        """ Detects the probability of animal existence in each image """
        from ibeis.model.detect import randomforest  # NOQ
        probexist_list = randomforest.detect_existence(ibs, gid_list, **kwargs)
        # Return for user inspection
        return probexist_list

    @default_decorator
    def detect_random_forest(ibs, gid_list, species, **kwargs):
        """ Runs animal detection in each image """
        # TODO: Return confidence here as well
        print('[ibs] detecting using random forests')
        from ibeis.model.detect import randomforest  # NOQ
        tt = ut.tic()
        detect_gen = randomforest.ibeis_generate_image_detections(ibs, gid_list, species, **kwargs)
        detected_gid_list, detected_bbox_list, detected_confidence_list, detected_img_confs = [], [], [], []
        ibs.cfg.other_cfg.ensure_attr('detect_add_after', 1)
        ADD_AFTER_THRESHOLD = ibs.cfg.other_cfg.detect_add_after

        def commit_detections(detected_gids, detected_bboxes, detected_confidences, img_confs):
            """ helper to commit detections on the fly """
            if len(detected_gids) == 0:
                return
            notes_list = ['rfdetect' for _ in range(len(detected_gid_list))]
            # Ideally, species will come from the detector with confidences that actually mean something
            species_list = [ibs.cfg.detect_cfg.species] * len(notes_list)
            ibs.add_annots(detected_gids, detected_bboxes,
                                notes_list=notes_list,
                                species_list=species_list,
                                detect_confidence_list=detected_confidences)

        # Adding new detections on the fly as they are generated
        for count, (gid, bbox, confidence, img_conf) in enumerate(detect_gen):
            detected_gid_list.append(gid)
            detected_bbox_list.append(bbox)
            detected_confidence_list.append(confidence)
            detected_img_confs.append(img_conf)
            # Save detections as we go, then reset lists
            if len(detected_gid_list) >= ADD_AFTER_THRESHOLD:
                commit_detections(detected_gid_list,
                                  detected_bbox_list,
                                  detected_confidence_list,
                                  detected_img_confs)
                detected_gid_list  = []
                detected_bbox_list = []
                detected_confidence_list = []
                detected_img_confs = []
        # Save any leftover detections
        commit_detections(  detected_gid_list,
                            detected_bbox_list,
                            detected_confidence_list,
                            detected_img_confs)
        tt_total = float(ut.toc(tt))
        if len(gid_list) > 0:
            print('[ibs] finshed detecting, took %.2f seconds (avg. %.2f seconds per image)' %
                  (tt_total, tt_total / len(gid_list)))
        else:
            print('[ibs] finshed detecting')
    #
    #
    #-----------------------------
    # --- ENCOUNTER CLUSTERING ---
    #-----------------------------

    @ut.indent_func('[ibs.compute_encounters]')
    def compute_encounters(ibs):
        """ Clusters images into encounters """
        from ibeis.model.preproc import preproc_encounter
        print('[ibs] Computing and adding encounters.')
        gid_list = ibs.get_valid_gids(require_unixtime=False, reviewed=False)
        enctext_list, flat_gids = preproc_encounter.ibeis_compute_encounters(ibs, gid_list)
        print('[ibs] Finished computing, about to add encounter.')
        ibs.set_image_enctext(flat_gids, enctext_list)
        print('[ibs] Finished computing and adding encounters.')

    #
    #
    #-----------------------
    # --- IDENTIFICATION ---
    #-----------------------

    @default_decorator
    def get_recognition_database_aids(ibs):
        """
        DEPRECATE or refactor

        Returns:
            daid_list (list): testing recognition database annotations """
        # TODO: Depricate, use exemplars instead
        if 'daid_list' in ibs.temporary_state:
            daid_list = ibs.temporary_state['daid_list']
        else:
            daid_list = ibs.get_valid_aids()
        return daid_list

    def query_chips(ibs, qaid_list, daid_list=None, cfgdict=None,
                    use_cache=None, use_bigcache=None, qreq_=None,
                    return_request=False):
        if daid_list is None:
            daid_list = ibs.get_valid_aids()
        if return_request:
            qaid2_qres, qreq_ = ibs._query_chips4(
                qaid_list, daid_list, cfgdict=cfgdict, use_cache=use_cache,
                use_bigcache=use_bigcache, qreq_=qreq_, return_request=return_request)
            qres_list = [qaid2_qres[qaid] for qaid in qaid_list]
            return qres_list, qreq_
        else:
            qaid2_qres = ibs._query_chips4(
                qaid_list, daid_list, cfgdict=cfgdict, use_cache=use_cache,
                use_bigcache=use_bigcache, qreq_=qreq_, return_request=return_request)
            qres_list = [qaid2_qres[qaid] for qaid in qaid_list]
            return qres_list

    def _query_chips4(ibs, qaid_list, daid_list, use_cache=None,
                      use_bigcache=None, return_request=False,
                      cfgdict=None, qreq_=None):
        """
        main entrypoint to submitting a query request

        Example:
            >>> # SLOW_DOCTEST
            >>> #from ibeis.all_imports import *  # NOQA
            >>> from ibeis.control.IBEISControl import *  # NOQA
            >>> qaid_list = [1]
            >>> daid_list = [1, 2, 3, 4, 5]
            >>> ibs = ibeis.test_main(db='testdb1')
            >>> qres = ibs._query_chips4(qaid_list, daid_list, use_cache=False)[1]

        #>>> qreq_ = mc4.get_ibeis_query_request(ibs, qaid_list, daid_list)
        #>>> qreq_.load_indexer()
        #>>> qreq_.load_query_vectors()
        #>>> qreq = ibs.qreq
        """
        from ibeis.model.hots import match_chips4 as mc4
        assert len(daid_list) > 0, 'there are no database chips'
        assert len(qaid_list) > 0, 'there are no query chips'
        if qreq_ is not None:
            import numpy as np
            assert np.all(qreq_.get_external_qaids() == qaid_list)
            assert np.all(qreq_.get_external_daids() == daid_list)

        res = qaid2_qres, qreq_ = mc4.submit_query_request(
            ibs,  qaid_list, daid_list, use_cache, use_bigcache,
            return_request=return_request, cfgdict=cfgdict, qreq_=qreq_)

        if return_request:
            qaid2_qres, qreq_ = res
            return qaid2_qres, qreq_
        else:
            qaid2_qres = res
            return qaid2_qres

    #_query_chips = _query_chips3
    _query_chips = _query_chips4

    @default_decorator
    def query_encounter(ibs, qaid_list, eid, **kwargs):
        """ _query_chips wrapper """
        daid_list = ibs.get_encounter_aids(eid)  # encounter database chips
        qaid2_qres = ibs._query_chips4(qaid_list, daid_list, **kwargs)
        # HACK IN ENCOUNTER INFO
        for qres in six.itervalues(qaid2_qres):
            qres.eid = eid
        return qaid2_qres

    @default_decorator
    def query_exemplars(ibs, qaid_list, **kwargs):
        """ Queries vs the exemplars """
        daid_list = ibs.get_valid_aids(is_exemplar=True)
        assert len(daid_list) > 0, 'there are no exemplars'
        return ibs._query_chips4(qaid_list, daid_list, **kwargs)

    @default_decorator
    def query_all(ibs, qaid_list, **kwargs):
        """ Queries vs the exemplars """
        daid_list = ibs.get_valid_aids()
        qaid2_qres = ibs._query_chips4(qaid_list, daid_list, **kwargs)
        return qaid2_qres


if __name__ == '__main__':
    """
    Issue when running on windows:
    python ibeis/control/IBEISControl.py
    python -m ibeis.control.IBEISControl --verbose --very-verbose --veryverbose --nodyn --quietclass

    CommandLine:
        python -m ibeis.control.IBEISControl
        python -m ibeis.control.IBEISControl --allexamples
        python -m ibeis.control.IBEISControl --allexamples --noface --nosrc
    """
    #from ibeis.control import IBEISControl
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
