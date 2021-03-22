##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Catalog
"""
import BTrees
import zope.index.interfaces
from zope import component
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.container.btree import BTreeContainer
from zope.container.interfaces import IObjectAddedEvent
from zope.interface import implementer
from zope.intid.interfaces import IIntIds, IIntIdAddedEvent, IIntIdRemovedEvent
from zope.lifecycleevent import IObjectModifiedEvent
from zope.location import location
from zope.location.interfaces import ILocationInfo

from zope.catalog.interfaces import ICatalog, INoAutoIndex, INoAutoReindex
from zope.catalog.interfaces import ICatalogIndex


class ResultSet:
    """Lazily accessed set of objects."""

    def __init__(self, uids, uidutil):
        self.uids = uids
        self.uidutil = uidutil

    def __len__(self):
        return len(self.uids)

    def __iter__(self):
        for uid in self.uids:
            obj = self.uidutil.getObject(uid)
            yield obj


@implementer(ICatalog,
             IAttributeAnnotatable,
             zope.index.interfaces.IIndexSearch,
             )
class Catalog(BTreeContainer):

    family = BTrees.family32

    def __init__(self, family=None):
        super(Catalog, self).__init__()
        if family is not None:
            self.family = family

    def clear(self):
        for index in self.values():
            index.clear()

    def index_doc(self, docid, texts):
        """Register the data in indexes of this catalog."""
        for index in self.values():
            index.index_doc(docid, texts)

    def unindex_doc(self, docid):
        """Unregister the data from indexes of this catalog."""
        for index in self.values():
            index.unindex_doc(docid)

    def _visitSublocations(self):
        """Restricts the access to the objects that live within
        the nearest site if the catalog itself is locatable.
        """
        uidutil = None
        locatable = ILocationInfo(self, None)
        if locatable is not None:
            site = locatable.getNearestSite()
            sm = site.getSiteManager()
            uidutil = sm.queryUtility(IIntIds)
            if uidutil not in [c.component for c in sm.registeredUtilities()]:
                # we do not have a local inits utility
                uidutil = component.getUtility(IIntIds, context=self)
                for uid in uidutil:
                    obj = uidutil.getObject(uid)
                    if location.inside(obj, site):
                        yield uid, obj
                return
        if uidutil is None:
            uidutil = component.getUtility(IIntIds)
        for uid in uidutil:
            yield uid, uidutil.getObject(uid)

    def updateIndex(self, index):
        for uid, obj in self._visitSublocations():
            index.index_doc(uid, obj)

    def updateIndexes(self):
        for uid, obj in self._visitSublocations():
            for index in self.values():
                index.index_doc(uid, obj)

    def apply(self, query):
        results = []
        for index_name, index_query in query.items():
            index = self[index_name]
            r = index.apply(index_query)
            if r is None:
                continue
            if not r:
                # empty results
                return r
            results.append((len(r), r))

        if not results:
            # no applicable indexes, so catalog was not applicable
            return None

        results.sort(key=lambda x: x[0])  # order from smallest to largest

        _, result = results.pop(0)
        for _, r in results:
            _, result = self.family.IF.weightedIntersection(result, r)

        return result

    def searchResults(self, **searchterms):
        sort_index = searchterms.pop('_sort_index', None)
        limit = searchterms.pop('_limit', None)
        reverse = searchterms.pop('_reverse', False)
        results = self.apply(searchterms)
        if results is not None:
            if sort_index is not None:
                index = self[sort_index]
                if not zope.index.interfaces.IIndexSort.providedBy(index):
                    raise ValueError(
                        'Index %s does not support sorting.' %
                        sort_index)
                results = list(
                    index.sort(
                        results,
                        limit=limit,
                        reverse=reverse))
            else:
                if reverse or limit:
                    results = list(results)
                if reverse:
                    results.reverse()
                if limit:
                    del results[limit:]
            uidutil = component.getUtility(IIntIds)
            results = ResultSet(results, uidutil)
        return results


@component.adapter(ICatalogIndex, IObjectAddedEvent)
def indexAdded(index, event):
    """When an index is added to a catalog, we have to index existing objects

       When an index is added, we tell it's parent to index it:

         >>> class FauxCatalog:
         ...     updated = None
         ...     def updateIndex(self, index):
         ...         self.updated = index

         >>> class FauxIndex:
         ...     pass

         >>> index = FauxIndex()
         >>> index.__parent__ = FauxCatalog()

         >>> from zope.catalog.catalog import indexAdded
         >>> indexAdded(index, None)
         >>> index.__parent__.updated is index
         True
       """
    index.__parent__.updateIndex(index)


@component.adapter(IIntIdAddedEvent)
def indexDocSubscriber(event):
    """A subscriber to IntIdAddedEvent"""
    ob = event.object
    if INoAutoIndex.providedBy(ob):
        return
    for cat in component.getAllUtilitiesRegisteredFor(ICatalog, context=ob):
        id = component.getUtility(IIntIds, context=cat).getId(ob)
        cat.index_doc(id, ob)


@component.adapter(IObjectModifiedEvent)
def reindexDocSubscriber(event):
    """A subscriber to ObjectModifiedEvent"""
    ob = event.object
    if INoAutoReindex.providedBy(ob):
        return
    for cat in component.getAllUtilitiesRegisteredFor(ICatalog, context=ob):
        id = component.getUtility(IIntIds, context=cat).queryId(ob)
        if id is not None:
            cat.index_doc(id, ob)


@component.adapter(IIntIdRemovedEvent)
def unindexDocSubscriber(event):
    """A subscriber to IntIdRemovedEvent"""
    ob = event.object
    for cat in component.getAllUtilitiesRegisteredFor(ICatalog, context=ob):
        id = component.getUtility(IIntIds, context=cat).queryId(ob)
        if id is not None:
            cat.unindex_doc(id)
