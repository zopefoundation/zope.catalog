##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""Text catalog indexes
"""
import zope.index.text
import zope.index.text.interfaces
import zope.interface

import zope.catalog.attribute
import zope.catalog.interfaces
import zope.container.contained
from zope.i18nmessageid import ZopeMessageFactory as _

class ITextIndex(zope.catalog.interfaces.IAttributeIndex,
                 zope.catalog.interfaces.ICatalogIndex):
    """Interface-based catalog text index
    """

    interface = zope.schema.Choice(
        title=_(u"Interface"),
        description=_(u"Objects will be adapted to this interface"),
        vocabulary=_("Interfaces"),
        required=False,
        default=zope.index.text.interfaces.ISearchableText,
        )

    field_name = zope.schema.BytesLine(
        title=_(u"Field Name"),
        description=_(u"Name of the field to index"),
        default="getSearchableText"
        )

    field_callable = zope.schema.Bool(
        title=_(u"Field Callable"),
        description=_(u"If true, then the field should be called to get the "
                      u"value to be indexed"),
        default=True,
        )

class TextIndex(zope.catalog.attribute.AttributeIndex,
                zope.index.text.TextIndex,
                zope.container.contained.Contained):

    zope.interface.implements(ITextIndex)
