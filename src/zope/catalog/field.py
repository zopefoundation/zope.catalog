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
"""Field catalog indexes
"""
import zope.index.field
import zope.interface

import zope.catalog.attribute
import zope.catalog.interfaces
import zope.container.contained


class IFieldIndex(zope.catalog.interfaces.IAttributeIndex,
                  zope.catalog.interfaces.ICatalogIndex):
    """Interface-based catalog field index
    """


@zope.interface.implementer(IFieldIndex)
class FieldIndex(zope.catalog.attribute.AttributeIndex,
                 zope.index.field.FieldIndex,
                 zope.container.contained.Contained):
    """
    Default implementation of a :class:`IFieldIndex`.
    """
