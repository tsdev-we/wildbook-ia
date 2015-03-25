"""
TODO:
    I've decided that I dont like the plural function names.
    We will move to singular function names.

CommandLine:
    # Regenerate command
    python ibeis/templates/template_generator.py
    python ibeis/templates/template_generator.py --dump-autogen-controller
"""
import utool as ut


#
#
#-----------------
# --- HEADER ---
#-----------------


Theader_ibeiscontrol = ut.codeblock(
    r'''
    # STARTBLOCK
    """
    Autogenerated IBEISController functions

    TemplateInfo:
        autogen_time = {timestamp}
        autogen_key = {autogen_key}

    ToRegenerate:
        # REM python -m ibeis.templates.template_generator --key {autogen_key}
        # REM python -m ibeis.templates.template_generator --key {autogen_key} --write
        python -m ibeis.templates.template_generator {argv_tail_str1}
        python -m ibeis.templates.template_generator {argv_tail_str2}
    """
    from __future__ import absolute_import, division, print_function
    import functools  # NOQA
    import six  # NOQA
    from six.moves import map, range, zip  # NOQA
    from ibeis import constants as const
    # REM dont circular import
    # REM from ibeis.control.IBEISControl import IBEISController
    import utool as ut
    from ibeis.control import controller_inject
    from ibeis.control import accessor_decors  # NOQA
    print, print_, printDBG, rrr, profile = ut.inject(__name__, '[autogen_{autogen_key}]')

    # Create dectorator to inject functions in this module into the IBEISController
    CLASS_INJECT_KEY, register_ibs_method = controller_inject.make_ibs_register_decorator(__name__)
    register_route = controller_inject.get_ibeis_flask_route()


    # REM def get_autogen_testdata():
    def testdata_ibs(defaultdb='testdb1'):
        import ibeis
        ibs = ibeis.opendb(defaultdb=defaultdb)
        config2_ = None  # qreq_.qparams
        return ibs, config2_

    # ENDBLOCK
    ''')


#
#
#-----------------
# --- ADDERS ---
#-----------------

"""
CommandLine:
    python -c "import utool as ut; ut.write_modscript_alias('Tgen.sh', 'ibeis.templates.template_generator')"
    sh Tgen.sh --key chip --Tcfg with_setters=False with_getters=False  with_adders=True
    sh Tgen.sh --key feat --Tcfg with_setters=False with_getters=False  with_adders=True
    sh Tgen.sh --key featweight --Tcfg with_setters=False with_getters=False  with_adders=True
"""
Tadder_pl_dependant = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @adder
    def add_{parent}_{leaf}({self}, {parent}_rowid_list, config2_=None, verbose=not ut.QUIET, return_num_dirty=False):
        """ {parent}.{leaf}.add({parent}_rowid_list)

        CRITICAL FUNCTION MUST EXIST FOR ALL DEPENDANTS
        Adds / ensures / computes a dependant property

        Args:
             {parent}_rowid_list

        Returns:
            returns {leaf}_rowid_list of added (or already existing {leaf}s)

        TemplateInfo:
            Tadder_pl_dependant
            parent = {parent}
            leaf = {leaf}

        Example0:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            # REM >>> {root}_rowid_list = {self}._get_all_{root}_rowids()[:2]
            # REM HACK
            >>> from ibeis import constants as const
            >>> {root}_rowid_list = {self}.get_valid_{root}_rowids(species=const.Species.ZEB_PLAIN)[:2]
            >>> if '{root}' != '{parent}':
            ...     {parent}_rowid_list = {self}.get_{root}_{parent}_rowid({root}_rowid_list, config2_=config2_, ensure=True)
            >>> {leaf}_rowid_list = {self}.add_{parent}_{leaf}({parent}_rowid_list, config2_=config2_)
            >>> assert len({leaf}_rowid_list) == len({parent}_rowid_list)
            >>> ut.assert_all_not_None({leaf}_rowid_list)

        Example1:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs('PZ_MTEST')
            >>> from ibeis import constants as const
            >>> {root}_rowid_list = {self}.get_valid_{root}_rowids(species=const.Species.ZEB_PLAIN)[0:7]
            >>> if '{root}' != '{parent}':
            ...     {parent}_rowid_list = {self}.get_{root}_{parent}_rowid({root}_rowid_list, config2_=config2_, ensure=True)
            >>> sub_{parent}_rowid_list1 = {parent}_rowid_list[0:6]
            >>> sub_{parent}_rowid_list2 = {parent}_rowid_list[5:7]
            >>> sub_{parent}_rowid_list3 = {parent}_rowid_list[0:7]
            >>> sub_{leaf}_rowid_list1 = {self}.get_{parent}_{leaf}_rowid(sub_{parent}_rowid_list1, config2_=config2_, ensure=True)
            >>> {self}.get_{parent}_{leaf}_rowid(sub_{parent}_rowid_list1, config2_=config2_, ensure=True)
            >>> sub_{leaf}_rowid_list1, num_dirty0 = {self}.add_{parent}_{leaf}(sub_{parent}_rowid_list1, config2_=config2_, return_num_dirty=True)
            >>> assert num_dirty0 == 0
            >>> ut.assert_all_not_None(sub_{leaf}_rowid_list1)
            >>> {self}.delete_{parent}_{leaf}(sub_{parent}_rowid_list2)
            >>> #{self}.delete_{parent}_{leaf}(sub_{parent}_rowid_list2)?
            >>> sub_{leaf}_rowid_list3 = {self}.get_{parent}_{leaf}_rowid(sub_{parent}_rowid_list3, config2_=config2_, ensure=False)
            >>> # Only the last two should be None
            >>> ut.assert_all_not_None(sub_{leaf}_rowid_list3[0:5], 'sub_{leaf}_rowid_list3[0:5])')
            >>> ut.assert_eq(sub_{leaf}_rowid_list3[5:7], [None, None])
            >>> sub_{leaf}_rowid_list3_ensured, num_dirty1 = {self}.add_{parent}_{leaf}(sub_{parent}_rowid_list3, config2_=config2_,  return_num_dirty=True)
            >>> ut.assert_eq(num_dirty1, 2, 'Only two params should have been computed here')
            >>> ut.assert_all_not_None(sub_{leaf}_rowid_list3_ensured)
        """
        #REM raise NotImplementedError('this code is a stub, you must populate it')
        from ibeis.model.preproc import preproc_{leaf}
        ut.assert_all_not_None({parent}_rowid_list, ' {parent}_rowid_list')
        # Get requested configuration id
        config_rowid = {self}.get_{leaf}_config_rowid(config2_=config2_)
        # Find leaf rowids that need to be computed
        initial_{leaf}_rowid_list = get_{parent}_{leaf}_rowids_({self}, {parent}_rowid_list, config2_=config2_)
        # Get corresponding "dirty" parent rowids
        isdirty_list = ut.flag_None_items(initial_{leaf}_rowid_list)
        dirty_{parent}_rowid_list = ut.filter_items({parent}_rowid_list, isdirty_list)
        num_dirty = len(dirty_{parent}_rowid_list)
        num_total = len({parent}_rowid_list)
        if num_dirty > 0:
            if verbose:
                fmtstr = '[add_{parent}_{leaf}s] adding %d / %d new {leaf} for config_rowid=%r'
                print(fmtstr % (num_dirty, num_total, config_rowid))
            # Dependant columns do not need true from_superkey getters.
            # We can use the Tgetter_pl_dependant_rowids_ instead
            get_rowid_from_superkey = functools.partial({self}.get_{parent}_{leaf}_rowids_, config2_=config2_)
            # REM proptup_gen = preproc_{leaf}.add_{leaf}_params_gen({self}, {parent}_rowid_list)
            proptup_gen = preproc_{leaf}.generate_{leaf}_properties({self}, dirty_{parent}_rowid_list, config2_=config2_)
            dirty_params_iter = (
                ({parent}_rowid, config_rowid, {leaf_other_propnames})
                for {parent}_rowid, ({leaf_other_propnames},) in
                zip(dirty_{parent}_rowid_list, proptup_gen)
            )
            colnames = {nonprimary_leaf_colnames}
            #{leaf}_rowid_list = {self}.{dbself}.add_cleanly({LEAF_TABLE}, colnames, dirty_params_iter, get_rowid_from_superkey)
            {self}.{dbself}._add({LEAF_TABLE}, colnames, dirty_params_iter)
            # Now that the dirty params are added get the correct order of rowids
            {leaf}_rowid_list = get_rowid_from_superkey({parent}_rowid_list)
        else:
            {leaf}_rowid_list = initial_{leaf}_rowid_list
        if return_num_dirty:
            return {leaf}_rowid_list, num_dirty
        return {leaf}_rowid_list
    # ENDBLOCK
    '''
)

Tadder_native = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @adder
    def add_{tbl}({self}, {allcol_sig}):
        """
        Returns:
            returns {tbl}_rowid_list of added (or already existing {tbl}s)

        TemplateInfo:
            Tadder_native
            tbl = {tbl}
        """
        # WORK IN PROGRESS
        colnames = ({allCOLNAMES},)
        {null_checks}
        params_iter = (
            ({allcol_items},)
            for ({allcol_items},) in
            zip({allcol_args})
        )
        get_rowid_from_superkey = {self}.get_{tbl}_rowid_from_superkey
        # FIXME: encode superkey paramx
        superkey_paramx = (0, 1)
        {tbl}_rowid_list = {self}.{dbself}.add_cleanly({TABLE}, colnames, params_iter, get_rowid_from_superkey, superkey_paramx)
        return {tbl}_rowid_list
    # ENDBLOCK
    '''
)

Tadder_rl_dependant = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @adder
    def add_{root}_{leaf}({self}, {root}_rowid_list, config2_=None):
        """ {leaf}_rowid_list <- {root}.{leaf}.ensure({root}_rowid_list)

        Adds / ensures / computes a dependant property (convinience)

        Args:
            {root}_rowid_list

        Returns:
            {leaf}_rowid_list

        TemplateInfo:
            Tadder_rl_dependant
            root = {root}
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {root}_rowid_list = {self}._get_all_{root}_rowids()[:2]
            >>> {leaf}_rowid_list = {self}.add_{root}_{leaf}({root}_rowid_list, config2_=config2_)
            >>> assert len({leaf}_rowid_list) == len({root}_rowid_list)
            >>> ut.assert_all_not_None({leaf}_rowid_list)
        """
        {leaf_parent}_rowid_list = {self}.get_{root}_{leaf_parent}_rowid({root}_rowid_list, config2_=config2_, ensure=True)
        {leaf}_rowid_list = add_{leaf_parent}_{leaf}({self}, {leaf_parent}_rowid_list, config2_=config2_)
        return {leaf}_rowid_list
    # ENDBLOCK
    '''
)


#
#
#-----------------
# --- CONFIG ---
#-----------------

Tcfg_rowid_getter = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @ider
    def get_{leaf}_config_rowid({self}, config2_=None):
        """ {leaf}_cfg_rowid = {leaf}.config_rowid()

        returns config_rowid of the current configuration
        Config rowids are always ensured

        Returns:
            {leaf}_cfg_rowid

        TemplateInfo:
            Tcfg_rowid_getter
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {leaf}_cfg_rowid = {self}.get_{leaf}_config_rowid()
        """
        if config2_ is not None:
            #{leaf}_cfg_suffix = config2_.qparams.{leaf}_cfgstr
            {leaf}_cfg_suffix = config2_.get('{leaf}_cfgstr')
            assert {leaf}_cfg_suffix is not None
            # TODO store config_rowid in qparams
        else:
            {leaf}_cfg_suffix = {self}.cfg.{leaf}_cfg.get_cfgstr()
        {leaf}_cfg_rowid = {self}.add_config({leaf}_cfg_suffix)
        return {leaf}_cfg_rowid
    # ENDBLOCK
    '''
)


#
#
#-----------------
# --- DELETERS ---
#-----------------

# DELETER LINES
Tline_pc_dependant_delete = ut.codeblock(
    r'''
    # STARTBLOCK
    _{child}_rowid_list = get_{parent}_{child}_rowids_({self}, {parent}_rowid_list, config2_=config2_)
    {child}_rowid_list = ut.filter_Nones(_{child}_rowid_list)
    {self}.delete_{child}({child}_rowid_list)
    # ENDBLOCK
    '''
)


# DELETER RL_DEPEND
#{pc_dependant_delete_lines}
Tdeleter_rl_depenant = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @deleter
    # REM @cache_invalidator({ROOT_TABLE})
    def delete_{root}_{leaf}({self}, {root}_rowid_list, config2_=None):
        """ {root}.{leaf}.delete({root}_rowid_list)

        Args:
            {root}_rowid_list

        TemplateInfo:
            Tdeleter_rl_depenant
            root = {root}
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {root}_rowid_list = {self}._get_all_{root}_rowids()[:1]
            >>> # Ensure there are  some leafs to delete
            >>> {leaf}_rowid_list = ibs.get_{root}_{leaf}_rowid({root}_rowid_list, config2_=config2_, ensure=True)
            >>> num_deleted1 = {self}.delete_{root}_{leaf}({root}_rowid_list, config2_=config2_)
            >>> num_deleted2 = {self}.delete_{root}_{leaf}({root}_rowid_list, config2_=config2_)
            >>> # The first delete should remove everything
            >>> ut.assert_eq(num_deleted1, len({leaf}_rowid_list))
            >>> # The second delete should have removed nothing
            >>> ut.assert_eq(num_deleted2, 0)
        """
        if ut.VERBOSE:
            print('[{self}] deleting %d {root}s leaf nodes' % len({root}_rowid_list))
        # Delete any dependants
        _{leaf}_rowid_list = {self}.get_{root}_{leaf}_rowid({root}_rowid_list, config2_=config2_, ensure=False)
        {leaf}_rowid_list = ut.filter_Nones(_{leaf}_rowid_list)
        num_deleted = {self}.delete_{leaf}({leaf}_rowid_list)
        return num_deleted
    # ENDBLOCK
    '''
)


# DELETER RL_DEPEND
#pluralize?
#{pc_dependant_delete_lines}
Tdeleter_pl_depenant = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @deleter
    # REM @cache_invalidator({ROOT_TABLE})
    def delete_{parent}_{leaf}({self}, {parent}_rowid_list, config2_=None):
        """ {parent}.{leaf}.delete({parent}_rowid_list)

        Args:
            {parent}_rowid_list

        Returns:
             int: num_deleted

        TemplateInfo:
            Tdeleter_rl_depenant
            parent = {parent}
            leaf = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {parent}_rowid_list = {self}._get_all_{parent}_rowids()[:2]
            >>> {self}.delete_{parent}_{leaf}({parent}_rowid_list, config2_=config2_)
        """
        if ut.VERBOSE:
            print('[{self}] deleting %d {parent}s leaf nodes' % len({parent}_rowid_list))
        # Delete any dependants
        _{leaf}_rowid_list = {self}.get_{parent}_{leaf}_rowid({parent}_rowid_list, config2_=config2_, ensure=False)
        {leaf}_rowid_list = ut.filter_Nones(_{leaf}_rowid_list)
        num_deleted = {self}.delete_{leaf}({leaf}_rowid_list)
        return num_deleted
    # ENDBLOCK
    '''
)


# DELETER NATIVE
Tdeleter_native_tbl = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @deleter
    # REM @cache_invalidator({TABLE})
    def delete_{tbl}({self}, {tbl}_rowid_list, config2_=None):
        """ {tbl}.delete({tbl}_rowid_list)

        delete {tbl} rows

        Args:
            {tbl}_rowid_list

        Returns:
            int: num_deleted

        TemplateInfo:
            Tdeleter_native_tbl
            tbl = {tbl}

        Example:
            >>> # DISABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {tbl}_rowid_list = {self}._get_all_{tbl}_rowids()[:2]
            >>> num_deleted = {self}.delete_{tbl}({tbl}_rowid_list)
            >>> print('num_deleted = %r' % (num_deleted,))
        """
        #from ibeis.model.preproc import preproc_{tbl}
        {Tdeleter_native_tbl_import}
        if ut.VERBOSE:
            print('[{self}] deleting %d {tbl} rows' % len({tbl}_rowid_list))
        # Prepare: Delete externally stored data (if any)
        #preproc_{tbl}.on_delete({self}, {tbl}_rowid_list, config2_=config2_)
        {Tdeleter_native_tbl_on_delete}
        # Finalize: Delete self
        {self}.{dbself}.delete_rowids({TABLE}, {tbl}_rowid_list)
        num_deleted = len(ut.filter_Nones({tbl}_rowid_list))
        return num_deleted
    # ENDBLOCK
    '''
)

#
#
#-----------------
# --- IDERS ---
#-----------------


Tider_all_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @ider
    def _get_all_{tbl}_rowids({self}):
        """ all_{tbl}_rowids <- {tbl}.get_all_rowids()

        Returns:
            list_ (list): unfiltered {tbl}_rowids

        TemplateInfo:
            Tider_all_rowids
            tbl = {tbl}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {self}._get_all_{tbl}_rowids()
        """
        all_{tbl}_rowids = {self}.{dbself}.get_all_rowids({TABLE})
        return all_{tbl}_rowids
    # ENDBLOCK
    '''
)


# RL IDER ALL ROWID
Tider_rl_dependant_all_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{root}_{leaf}_all_rowids({self}, {root}_rowid_list, eager=True, nInput=None):
        """ {leaf}_rowid_list <- {root}.{leaf}.all_rowids([{root}_rowid_list])

        Gets {leaf} rowids of {root} under the current state configuration.

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tider_rl_dependant_all_rowids
            root = {root}
            leaf = {leaf}
        """
        # FIXME: broken
        colnames = ({LEAF_PARENT}_ROWID,)
        {leaf}_rowid_list = {self}.{dbself}.get(
            {LEAF_TABLE}, colnames, {root}_rowid_list,
            id_colname={ROOT}_ROWID, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')

#
#
#-----------------
# --- GETTERS ---
#-----------------

# LINES GETTER
Tline_pc_dependant_rowid = ut.codeblock(
    r'''
    # STARTBLOCK
    {child}_rowid_list = {self}.get_{parent}_{child}_rowid({parent}_rowid_list, config2_=config2_, ensure=ensure)
    # ENDBLOCK
    '''
)


# RL GETTER MULTICOLUMN
Tgetter_rl_pclines_dependant_multicolumn = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{root}_{multicol}({self}, {root}_rowid_list, config2_=None, ensure=True):
        """ {leaf}_rowid_list <- {root}.{leaf}.{multicol}s[{root}_rowid_list]

        Get {col} data of the {root} table using the dependant {leaf} table

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {col}_list

        TemplateInfo:
            Tgetter_rl_pclines_dependant_column
            root = {root}
            col  = {col}
            leaf = {leaf}

        Example:
            >>> # DISABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {root}_rowid_list = {self}._get_all_{root}_rowids()
            >>> {multicol}_list = {self}.get_{root}_{multicol}({root}_rowid_list, config2_=config2_)
            >>> assert len({multicol}_list) == len({root}_rowid_list)

        """
        # REM Get leaf rowids
        {pc_dependant_rowid_lines}
        # REM Get col values
        {multicol}_list = {self}.get_{leaf}_{multicol}({leaf}_rowid_list)
        return {multicol}_list
    # ENDBLOCK
    ''')


# NATIVE MULTICOLUMN GETTER
# eg. get_chip_sizes
Tgetter_native_multicolumn = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{tbl}_{multicol}({self}, {tbl}_rowid_list, eager=True):
        """
        Returns zipped tuple of information from {multicol} columns

        Tgetter_native_multicolumn

        Args:
            {tbl}_rowid_list (list):

        Returns:
            list: {multicol}_list

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {tbl}_rowid_list = {self}._get_all_{tbl}_rowids()
            >>> ensure = False
            >>> {multicol}_list = {self}.get_{tbl}_{multicol}({tbl}_rowid_list, eager=eager)
            >>> assert len({tbl}_rowid_list) == len({multicol}_list)
        """
        id_iter = {tbl}_rowid_list
        colnames = {MULTICOLNAMES}
        {multicol}_list  = {self}.{dbself}.get({TABLE}, colnames, id_iter, id_colname='rowid', eager=eager)
        return {multicol}_list
    # ENDBLOCK
    ''')

# RL GETTER COLUMN
Tgetter_rl_pclines_dependant_column = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{root}_{col}({self}, {root}_rowid_list, config2_=None, ensure=True):
        """ {leaf}_rowid_list <- {root}.{leaf}.{col}s[{root}_rowid_list]

        Get {col} data of the {root} table using the dependant {leaf} table

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {col}_list

        TemplateInfo:
            Tgetter_rl_pclines_dependant_column
            root = {root}
            col  = {col}
            leaf = {leaf}
        """
        # REM Get leaf rowids
        {pc_dependant_rowid_lines}
        # REM Get col values
        {col}_list = {self}.get_{leaf}_{col}({leaf}_rowid_list)
        return {col}_list
    # ENDBLOCK
    ''')

# NATIVE COLUMN GETTER
Tgetter_table_column = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{tbl}_{col}({self}, {tbl}_rowid_list, eager=True, nInput=None):
        """ {col}_list <- {tbl}.{col}[{tbl}_rowid_list]

        gets data from the "native" column "{col}" in the "{tbl}" table

        Args:
            {tbl}_rowid_list (list):

        Returns:
            list: {col}_list

        TemplateInfo:
            Tgetter_table_column
            col = {col}
            tbl = {tbl}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {tbl}_rowid_list = {self}._get_all_{tbl}_rowids()
            >>> eager = True
            >>> {col}_list = {self}.get_{tbl}_{col}({tbl}_rowid_list, eager=eager)
            >>> assert len({tbl}_rowid_list) == len({col}_list)
        """
        id_iter = {tbl}_rowid_list
        colnames = ({COLNAME},)
        {col}_list = {self}.{dbself}.get({TABLE}, colnames, id_iter, id_colname='rowid', eager=eager, nInput=nInput)
        return {col}_list
    # ENDBLOCK
    ''')


Tgetter_extern = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{tbl}_{externcol}({self}, {tbl}_rowid_list, eager=True, nInput=None):
        """ {externcol}_list <- {tbl}.{externcol}[{tbl}_rowid_list]

        Args:
            {tbl}_rowid_list (list):

        Returns:
            list: {externcol}_list

        TemplateInfo:
            Tgetter_extern
            tbl = {tbl}
            externtbl = {externtbl}
            externcol = {externcol}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {tbl}_rowid_list = {self}._get_all_{tbl}_rowids()
            >>> eager = True
            >>> {externcol}_list = {self}.get_{tbl}_{externcol}({tbl}_rowid_list, eager=eager)
            >>> assert len({tbl}_rowid_list) == len({externcol}_list)
        """
        {externtbl}_rowid_list = {self}.get_{tbl}_{externtbl}_rowid({tbl}_rowid_list, eager=eager, nInput=nInput)
        {externcol}_list = {self}.get_{externtbl}_{externcol}({externtbl}_rowid_list, eager=eager, nInput=nInput)
        return {externcol}_list
    # ENDBLOCK
    ''')

# RL GETTER ROWID
Tgetter_rl_dependant_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{root}_{leaf}_rowid({self}, {root}_rowid_list, config2_=None, ensure=True, eager=True, nInput=None):
        """ {leaf}_rowid_list <- {root}.{leaf}.rowids[{root}_rowid_list]

        Get {leaf} rowids of {root} under the current state configuration.

        Args:
            {root}_rowid_list (list):

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tgetter_rl_dependant_rowids
            root        = {root}
            leaf_parent = {leaf_parent}
            leaf        = {leaf}

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {root}_rowid_list = {self}._get_all_{root}_rowids()
            >>> {leaf}_rowid_list1 = {self}.get_{root}_{leaf}_rowid({root}_rowid_list, config2_, ensure=False)
            >>> {leaf}_rowid_list2 = {self}.get_{root}_{leaf}_rowid({root}_rowid_list, config2_, ensure=True)
            >>> {leaf}_rowid_list3 = {self}.get_{root}_{leaf}_rowid({root}_rowid_list, config2_, ensure=False)
            >>> print({leaf}_rowid_list1)
            >>> print({leaf}_rowid_list2)
            >>> print({leaf}_rowid_list3)
        """
        # REM if ensure:
        # REM    # Ensuring dependant columns is equivalent to adding cleanly
        # REM    return {self}.add_{root}_{leaf}({root}_rowid_list, config2_=config2_)
        # REM else:
        # Get leaf_parent rowids
        {leaf_parent}_rowid_list = {self}.get_{root}_{leaf_parent}_rowid({root}_rowid_list, config2_=config2_, ensure=ensure)
        {leaf}_rowid_list = get_{leaf_parent}_{leaf}_rowid({self}, {leaf_parent}_rowid_list, config2_=config2_, ensure=ensure)
        # REM colnames = ({LEAF}_ROWID,)
        # REM config_rowid = {self}.get_{leaf}_config_rowid(config2_=config2_)
        # REM andwhere_colnames = ({LEAF_PARENT}_ROWID, CONFIG_ROWID,)
        # REM params_iter = [({leaf_parent}_rowid, config_rowid,) for {leaf_parent}_rowid in {leaf_parent}_rowid_list]
        # REM {leaf}_rowid_list = {self}.{dbself}.get_where2(
        # REM   {LEAF_TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# PL GETTER ROWID WITHOUT ENSURE
Tgetter_pl_dependant_rowids_ = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{parent}_{leaf}_rowids_({self}, {parent}_rowid_list, config2_=None, eager=True, nInput=None):
        """
        equivalent to get_{parent}_{leaf}_rowids_ except ensure is constrained
        to be False.

        Also you save a stack frame because get_{parent}_{leaf}_rowids just
        calls this function if ensure is False

        TemplateInfo:
            Tgetter_pl_dependant_rowids_
        """
        colnames = ({LEAF}_ROWID,)
        config_rowid = {self}.get_{leaf}_config_rowid(config2_=config2_)
        andwhere_colnames = ({PARENT}_ROWID, CONFIG_ROWID,)
        params_iter = (({parent}_rowid, config_rowid,) for {parent}_rowid in {parent}_rowid_list)
        {leaf}_rowid_list = {self}.{dbself}.get_where2(
            {LEAF_TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# PL GETTER ROWID WITH ENSURE
Tgetter_pl_dependant_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{parent}_{leaf}_rowid({self}, {parent}_rowid_list, config2_=None, ensure=True, eager=True, nInput=None):
        """ {leaf}_rowid_list <- {parent}.{leaf}.rowids[{parent}_rowid_list]

        get {leaf} rowids of {parent} under the current state configuration
        if ensure is True, this function is equivalent to add_{parent}_{leaf}s

        Args:
            {parent}_rowid_list (list):
            ensure (bool): default false

        Returns:
            list: {leaf}_rowid_list

        TemplateInfo:
            Tgetter_pl_dependant_rowids
            parent = {parent}
            leaf = {leaf}

        Timeit:
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> # Test to see if there is any overhead to injected vs native functions
            >>> %timeit get_{parent}_{leaf}_rowid({self}, {parent}_rowid_list)
            >>> %timeit {self}.get_{parent}_{leaf}_rowid({parent}_rowid_list)

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {parent}_rowid_list = {self}._get_all_{parent}_rowids()
            >>> ensure = False
            >>> {leaf}_rowid_list = {self}.get_{parent}_{leaf}_rowid({parent}_rowid_list, config2_, ensure)
            >>> assert len({leaf}_rowid_list) == len({parent}_rowid_list)
        """
        if ensure:
            {leaf}_rowid_list = add_{parent}_{leaf}({self}, {parent}_rowid_list, config2_=config2_)
        else:
            {leaf}_rowid_list = get_{parent}_{leaf}_rowids_(
                {self}, {parent}_rowid_list, config2_=config2_, eager=eager, nInput=nInput)
        return {leaf}_rowid_list
    # ENDBLOCK
    ''')


# NATIVE FROMSUPERKEY ROWID GETTER
#id_iter = (({tbl}_rowid,) for {tbl}_rowid in {tbl}_rowid_list)
Tgetter_native_rowid_from_superkey = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @getter
    def get_{tbl}_rowid_from_superkey({self}, {superkey_args}, eager=True, nInput=None):
        """ {tbl}_rowid_list <- {tbl}[{superkey_args}]

        Args:
            superkey lists: {superkey_args}

        Returns:
            {tbl}_rowid_list

        TemplateInfo:
            Tgetter_native_rowid_from_superkey
            tbl = {tbl}
        """
        colnames = ({TBL}_ROWID,)
        # FIXME: col_rowid is not correct
        params_iter = zip({superkey_args})
        andwhere_colnames = [{superkey_COLNAMES}]
        {tbl}_rowid_list = {self}.{dbself}.get_where2(
            {TABLE}, colnames, params_iter, andwhere_colnames, eager=eager, nInput=nInput)
        return {tbl}_rowid_list
    # ENDBLOCK
    ''')

#
#
#-----------------
# --- SETTERS ---
#-----------------


# NATIVE COL SETTER
Tsetter_native_column = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @setter
    def set_{tbl}_{col}({self}, {tbl}_rowid_list, {col}_list, duplicate_behavior='error'):
        """ {col}_list -> {tbl}.{col}[{tbl}_rowid_list]

        Args:
            {tbl}_rowid_list
            {col}_list

        TemplateInfo:
            Tsetter_native_column
            tbl = {tbl}
            col = {col}
        """
        id_iter = {tbl}_rowid_list
        colnames = ({COLNAME},)
        {self}.{dbself}.set({TABLE}, colnames, {col}_list, id_iter, duplicate_behavior=duplicate_behavior)
    # ENDBLOCK
    ''')


Tsetter_native_multicolumn = ut.codeblock(
    r'''
    # STARTBLOCK
    def set_{tbl}_{multicol}({self}, {tbl}_rowid_list, {multicol}_list, duplicate_behavior='error'):
        """ {multicol}_list -> {tbl}.{multicol}[{tbl}_rowid_list]

        Tsetter_native_multicolumn

        Args:
            {tbl}_rowid_list (list):

        Example:
            >>> # ENABLE_DOCTEST
            >>> from {autogen_modname} import *  # NOQA
            >>> {self}, config2_ = testdata_ibs()
            >>> {multicol}_list = get_{tbl}_{multicol}({self}, {tbl}_rowid_list)
        """
        id_iter = {tbl}_rowid_list
        colnames = {MULTICOLNAMES}
        {self}.{dbself}.set({TABLE}, colnames,  {multicol}_list, id_iter, duplicate_behavior=duplicate_behavior)
    # ENDBLOCK
    ''')

#
#
#-------------------------------
# --- UNFINISHED AND DEFERRED ---
#-------------------------------


Tdeleter_table1_relation = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @deleter
    def delete_{tbl1}_{relation_tbl}_relation({self}, {tbl1}_rowid_list):
        """
        Deletes the relationship between an {tbl1} and {tbl2}

        TemplateInfo:
            Tdeleter_relationship
            tbl = {relation_tbl}
        """
        {relation_tbl}_rowids_list = {self}.get_{tbl1}_{relation_tbl}_rowid({tbl1}_rowid_list)
        {relation_tbl}_rowid_list = ut.flatten({relation_tbl}_rowids_list)
        {self}.{dbself}.delete_rowids({RELATION_TABLE}, {relation_tbl}_rowid_list)
    # ENDBLOCK
    '''
)


Tgetter_table1_rowids = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @deleter
    def get_{tbl1}_{relation_tbl}_rowid({self}, {tbl1}_rowid_list):
        """
        Returns:
            list of lists: {relation_tbl}_rowids_list

        TemplateInfo:
            Tgetter_relationship
            tbl = {relation_tbl}
        """
        colnames = ('{relation_tbl}_rowid',)
        params_iter = {tbl1}_rowid_list
        where_clause = '{tbl2}_rowid=?'
        {relation_tbl}_rowids_list = ibs.db.get_where({RELATION_TABLE}, colnames, params_iter,
                                      where_clause, unpack_scalars=False)
        return {relation_tbl}_rowids_list
    # ENDBLOCK
    '''
)

Tadder_relationship = ut.codeblock(
    r'''
    # STARTBLOCK
    # REM @adder
    def add_{relation_tbl}_{tbl1}_{tbl2}_relation({self}, {tbl1}_rowid_list, {tbl2}_rowid_list):
        """
        Adds a relationship between an image and encounter

        Returns:
            {relation_tbl}_rowid_list

        TemplateInfo:
            Tadder_relationship
            tbl = {relation_tbl}
        """
        colnames = ('{tbl1}_rowid', '{tbl2}_rowid',)
        params_iter = list(zip({tbl1}_rowid_list, {tbl2}_rowid_list))
        get_rowid_from_superkey = {self}.get_{relation_tbl}_rowid_from_superkey
        superkey_paramx = (0, 1)
        {relation_tbl}_rowid_list = {self}.{dbself}.add_cleanly(
            {RELATION_TABLE}, colnames, params_iter, get_rowid_from_superkey, superkey_paramx)
        return {relation_tbl}_rowid_list
    # ENDBLOCK
    ''')


#
#
#-----------------
# --- FOOTER ---
#-----------------


Tfooter_ibeiscontrol = ut.codeblock(
    r'''
    # STARTBLOCK
    if __name__ == '__main__':
        """
        {main_docstr_body}
        """
        import multiprocessing
        multiprocessing.freeze_support()
        import utool as ut
        ut.doctest_funcs()
    # ENDBLOCK
    ''')
