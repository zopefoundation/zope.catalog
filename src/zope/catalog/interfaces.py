##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Catalog Interfaces
"""

import zope.index.interfaces
import zope.interface
import zope.schema
import zope.container.interfaces
import zope.container.constraints

from zope.i18nmessageid import ZopeMessageFactory as _


class ICatalogQuery(zope.interface.Interface):
    """Provides Catalog Queries."""

    def searchResults(**kw):
        """Search on the given indexes.

        Keyword arguments dictionary keys
        are index names and values are queries
        for these indexes.

        Keyword arguments has some special names,
        used by the catalog itself:

         * _sort_index - The name of index to sort
           results with. This index must implement
           zope.index.interfaces.IIndexSort.
         * _limit - Limit result set by this number,
           useful when used with sorting.
         * _reverse - Reverse result set, also
           useful with sorting.

        """


class ICatalogEdit(zope.index.interfaces.IInjection):
    """Allows one to manipulate the Catalog information."""

    def updateIndexes():
        """Reindex all objects."""


class ICatalogIndex(zope.index.interfaces.IInjection,
                    zope.index.interfaces.IIndexSearch,
                    ):
    """An index to be used in a catalog
    """

    __parent__ = zope.schema.Field()

    zope.container.constraints.containers('.ICatalog')


class ICatalog(ICatalogQuery, ICatalogEdit,
               zope.container.interfaces.IContainer):
    """Marker to describe a catalog in content space."""

    zope.container.constraints.contains(ICatalogIndex)


class IAttributeIndex(zope.interface.Interface):
    """I index objects by first adapting them to an interface, then
       retrieving a field on the adapted object.
    """

    interface = zope.schema.Choice(
        title=_(u"Interface"),
        description=_(u"Objects will be adapted to this interface"),
        vocabulary="Interfaces",
        required=False,
    )

    field_name = zope.schema.NativeStringLine(
        title=_(u"Field Name"),
        description=_(u"Name of the field to index"),
    )

    field_callable = zope.schema.Bool(
        title=_(u"Field Callable"),
        description=_(u"If true, then the field should be called to get the "
                      u"value to be indexed"),
    )


class INoAutoIndex(zope.interface.Interface):
    """Marker for objects that should not be automatically indexed"""


class INoAutoReindex(zope.interface.Interface):
    """Marker for objects that should not be automatically reindexed"""
