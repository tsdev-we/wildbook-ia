# -*- coding: utf-8 -*-
"""
This provides concrete classes which inherit from abstract
api_item_models/api_table_models/api_tree_models in guitool.
"""
from __future__ import absolute_import, division, print_function
import utool as ut
from guitool import (APIItemModel, APITableView, APITreeView, APIItemWidget,
                     StripeProxyModel, ChangeLayoutContext)
print, print_, printDBG, rrr, profile = ut.inject(__name__, '[newgui_models]')

#---------------------
# --- IBEIS Tables ---
#---------------------


class IBEISTableWidget(APIItemWidget):
    def __init__(widget, headers=None, parent=None, *args):
        widget.ibswin = parent
        widget.imgsetid = None
        APIItemWidget.__init__(widget, headers=headers, parent=parent,
                                model_class=IBEISStripeModel,
                                view_class=IBEISTableView)


class IBEISTreeWidget(APIItemWidget):
    def __init__(widget, headers=None, parent=None, *args):
        widget.ibswin = parent
        widget.imgsetid = None
        APIItemWidget.__init__(widget, headers=headers, parent=parent,
                                model_class=IBEISItemModel,
                                view_class=IBEISTreeView)


IBEISSTRIPEMODEL_BASE = StripeProxyModel
#IBEISSTRIPEMODEL_BASE = APIItemModel
IBEISITEMMODEL_BASE = APIItemModel


class IBEISStripeModel(IBEISSTRIPEMODEL_BASE):
    def __init__(model, headers=None, parent=None, *args):
        IBEISSTRIPEMODEL_BASE.__init__(model, parent=parent, numduplicates=1, *args)
        model.ibswin = parent
        model.imgsetid = -1  # negative one is an invalid imgsetid
        model.original_ider = None
        if IBEISSTRIPEMODEL_BASE == StripeProxyModel:
            model.sourcemodel = APIItemModel(parent=parent)
            model.setSourceModel(model.sourcemodel)
            if ut.VERBOSE:
                print('[ibs_model] just set the sourcemodel')

    def _update_headers(model, **headers):
        def _null_ider(**kwargs):
            return []
        model.original_iders = headers.get('iders', [_null_ider])
        if len(model.original_iders) > 0:
            model.new_iders = model.original_iders[:]
            model.new_iders[0] = model._ider
        headers['iders'] = model.new_iders
        model._nd = headers.get('num_duplicates', 1)
        model.sourcemodel._update_headers(**headers)
        #return IBEISSTRIPEMODEL_BASE._update_headers(model, **headers)

    def _ider(model):
        """ Overrides the API model ider to give only selected imageset ids """
        return model.original_iders[0](imgsetid=model.imgsetid)

    def _change_imageset(model, imgsetid):
        model.imgsetid = imgsetid
        with ChangeLayoutContext([model]):
            IBEISSTRIPEMODEL_BASE._update_rows(model)


class IBEISTableView(APITableView):
    """
    View for ANNOTATION / NAME / IMAGE Tables
    """
    def __init__(tblview, parent=None):
        APITableView.__init__(tblview, parent)
        tblview.ibswin = parent

    def _change_imageset(tblview, imgsetid):
        tblview.verticalScrollBar().setSliderPosition(0)
        model = tblview.model()
        if model is not None:
            model._change_imageset(imgsetid)


class IBEISItemModel(IBEISITEMMODEL_BASE):
    def __init__(model, headers=None, parent=None, *args):
        IBEISITEMMODEL_BASE.__init__(model, parent=parent, *args)
        model.ibswin = parent
        model.imgsetid = -1
        model.original_ider = None

    def _update_headers(model, **headers):
        """
        filter the iders
        """
        def _null_ider(**kwargs):
            return []
        model.original_iders = headers.get('iders', [_null_ider])
        if len(model.original_iders) > 0:
            model.new_iders = model.original_iders[:]
            model.new_iders[0] = model._ider
        headers['iders'] = model.new_iders
        return IBEISITEMMODEL_BASE._update_headers(model, **headers)

    def _ider(model):
        """
        Overrides the API model ider to give filtered output,
        ie: only selected imageset ids
        """
        return model.original_iders[0](imgsetid=model.imgsetid)

    def _change_imageset(model, imgsetid):
        model.imgsetid = imgsetid
        with ChangeLayoutContext([model]):
            IBEISITEMMODEL_BASE._update_rows(model)


class IBEISTreeView(APITreeView):
    """
    View for NAME / ANNOTATION Tree
    """
    def __init__(treeview, parent=None):
        APITreeView.__init__(treeview, parent)
        treeview.ibswin = parent

    def _change_imageset(treeview, imgsetid):
        treeview.verticalScrollBar().setSliderPosition(0)
        model = treeview.model()
        if model is not None:
            # FIXME: should defer the change of imageset until
            # the view becomes visible
            model._change_imageset(imgsetid)


#-------------------------
# --- IMAGESET TABLES ---
#-------------------------


class ImagesetTableWidget(APIItemWidget):
    def __init__(widget, headers=None, parent=None, *args):
        widget.ibswin = parent
        APIItemWidget.__init__(widget, headers=headers, parent=parent,
                                model_class=ImagesetTableModel,
                                view_class=ImagesetTableView)


class ImagesetTableModel(APIItemModel):
    def __init__(model, headers=None, parent=None):
        model.ibswin = parent
        model.headers = headers
        APIItemModel.__init__(model, headers=headers, parent=parent)


class ImagesetTableView(APITableView):
    """
    View for ImageSet Table
    """
    def __init__(tblview, parent=None):
        APITableView.__init__(tblview, parent)
        tblview.ibswin = parent
        #tblview.setMaximumSize(500, 9999)
