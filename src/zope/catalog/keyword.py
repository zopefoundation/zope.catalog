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
"""Keyword catalog index
"""
import zope.index.keyword
import zope.interface

import zope.container.contained
import zope.catalog.attribute
import zope.catalog.interfaces


class IKeywordIndex(zope.catalog.interfaces.IAttributeIndex,
                    zope.catalog.interfaces.ICatalogIndex):
    """Interface-based catalog keyword index"""


@zope.interface.implementer(IKeywordIndex)
class KeywordIndex(zope.catalog.attribute.AttributeIndex,
                   zope.index.keyword.KeywordIndex,
                   zope.container.contained.Contained):
    """
    Default implementation of :class:`IKeywordIndex`.
    """


@zope.interface.implementer(IKeywordIndex)
class CaseInsensitiveKeywordIndex(
        zope.catalog.attribute.AttributeIndex,
        zope.index.keyword.CaseInsensitiveKeywordIndex,
        zope.container.contained.Contained):
    """
    A kind of :class:`IKeywordIndex` that is not sensitive to case.
    """
