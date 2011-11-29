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
"""Tests for catalog

Note that indexes &c already have test suites, we only have to check that
a catalog passes on events that it receives.
"""
import unittest
from zope.testing import doctest
from zope.interface import implements, Interface
from zope.interface.verify import verifyObject
from BTrees.IFBTree import IFSet
from zope.intid.interfaces import IIntIds
from zope.location.location import Location
from zope.component import provideUtility
from zope.component import provideAdapter
from zope.component import provideHandler
from zope.component import testing, eventtesting
from zope.component.interfaces import ISite, IComponentLookup
from zope.site.hooks import setSite, setHooks, resetHooks
from zope.site.folder import Folder, rootFolder
from zope.site.site import SiteManagerAdapter, LocalSiteManager
from zope.traversing import api
from zope.traversing.testing import setUp as traversingSetUp
from zope.traversing.interfaces import ITraversable
from zope.container.traversal import ContainerTraversable
from zope.container.interfaces import ISimpleReadContainer

from zope.index.interfaces import IInjection, IIndexSearch
from zope.catalog.interfaces import ICatalog
from zope.catalog.catalog import Catalog
from zope.catalog.field import FieldIndex


class ReferenceStub:
    def __init__(self, obj):
        self.obj = obj

    def __call__(self):
        return self.obj


class IntIdsStub:
    """A stub for IntIds."""
    implements(IIntIds)

    def __init__(self):
        self.ids = {}
        self.objs = {}
        self.lastid = 0

    def _generateId(self):
        self.lastid += 1
        return self.lastid

    def register(self, ob):
        if ob not in self.ids:
            uid = self._generateId()
            self.ids[ob] = uid
            self.objs[uid] = ob
            return uid
        else:
            return self.ids[ob]

    def unregister(self, ob):
        uid = self.ids[ob]
        del self.ids[ob]
        del self.objs[uid]

    def getObject(self, uid):
        return self.objs[uid]

    def getId(self, ob):
        return self.ids[ob]

    def queryId(self, ob, default=None):
        return self.ids.get(ob, default)

    def __iter__(self):
        return self.objs.iterkeys()


class StubIndex:
    """A stub for Index."""

    implements(IIndexSearch, IInjection)

    def __init__(self, field_name, interface=None):
        self._field_name = field_name
        self.interface = interface
        self.doc = {}

    def index_doc(self, docid, obj):
        self.doc[docid] = obj

    def unindex_doc(self, docid):
        del self.doc[docid]

    def apply(self, term):
        results = []
        for docid in self.doc:
            obj = self.doc[docid]
            fieldname = getattr(obj, self._field_name, '')
            if fieldname == term:
                results.append(docid)
        return IFSet(results)


class stoopid:
    def __init__(self, **kw):
        self.__dict__ = kw


class PlacelessSetup(testing.PlacelessSetup,
                     eventtesting.PlacelessSetup):

    def setUp(self, doctesttest=None):
        testing.PlacelessSetup.setUp(self)
        eventtesting.PlacelessSetup.setUp(self)


class Test(PlacelessSetup, unittest.TestCase):

    def test_catalog_add_del_indexes(self):
        catalog = Catalog()
        verifyObject(ICatalog, catalog)
        index = StubIndex('author', None)
        catalog['author'] = index
        self.assertEqual(list(catalog.keys()), ['author'])
        index = StubIndex('title', None)
        catalog['title'] = index
        indexes = list(catalog.keys())
        indexes.sort()
        self.assertEqual(indexes, ['author', 'title'])
        del catalog['author']
        self.assertEqual(list(catalog.keys()), ['title'])

    def _frob_intidutil(self, ints=True, apes=True):
        uidutil = IntIdsStub()
        provideUtility(uidutil, IIntIds)
        # whack some objects in our little objecthub
        if ints:
            for i in range(10):
                uidutil.register("<object %s>"%i)
        if apes:
            uidutil.register(stoopid(simiantype='monkey', name='bobo'))
            uidutil.register(stoopid(simiantype='monkey', name='bubbles'))
            uidutil.register(stoopid(simiantype='monkey', name='ginger'))
            uidutil.register(stoopid(simiantype='bonobo', name='ziczac'))
            uidutil.register(stoopid(simiantype='bonobo', name='bobo'))
            uidutil.register(stoopid(simiantype='punyhuman', name='anthony'))
            uidutil.register(stoopid(simiantype='punyhuman', name='andy'))
            uidutil.register(stoopid(simiantype='punyhuman', name='kev'))

    def test_updateindexes(self):
        """Test a full refresh."""
        self._frob_intidutil()
        catalog = Catalog()
        catalog['author'] = StubIndex('author', None)
        catalog['title'] = StubIndex('author', None)
        catalog.updateIndexes()
        for index in catalog.values():
            checkNotifies = index.doc
            self.assertEqual(len(checkNotifies), 18)

    def test_updateindex(self):
        """Test a full refresh."""
        self._frob_intidutil()
        catalog = Catalog()
        catalog['author'] = StubIndex('author', None)
        catalog['title'] = StubIndex('author', None)
        catalog.updateIndex(catalog['author'])
        checkNotifies = catalog['author'].doc
        self.assertEqual(len(checkNotifies), 18)
        checkNotifies = catalog['title'].doc
        self.assertEqual(len(checkNotifies), 0)

    def test_basicsearch(self):
        """Test the simple search results interface."""
        self._frob_intidutil(ints=0)
        catalog = Catalog()
        catalog['simiantype'] = StubIndex('simiantype', None)
        catalog['name'] = StubIndex('name', None)
        catalog.updateIndexes()

        res = catalog.searchResults(simiantype='monkey')
        names = [x.name for x in res]
        names.sort()
        self.assertEqual(len(names), 3)
        self.assertEqual(names, ['bobo', 'bubbles', 'ginger'])

        res = catalog.searchResults(name='bobo')
        names = [x.simiantype for x in res]
        names.sort()
        self.assertEqual(len(names), 2)
        self.assertEqual(names, ['bonobo', 'monkey'])

        res = catalog.searchResults(simiantype='punyhuman', name='anthony')
        self.assertEqual(len(res), 1)
        ob = iter(res).next()
        self.assertEqual((ob.name, ob.simiantype), ('anthony', 'punyhuman'))

        res = catalog.searchResults(simiantype='ape', name='bobo')
        self.assertEqual(len(res), 0)

        res = catalog.searchResults(simiantype='ape', name='mwumi')
        self.assertEqual(len(res), 0)
        self.assertRaises(KeyError, catalog.searchResults,
                          simiantype='monkey', hat='beret')


class CatalogStub:
    implements(ICatalog)
    def __init__(self):
        self.regs = []
        self.unregs = []

    def index_doc(self, docid, doc):
        self.regs.append((docid, doc))

    def unindex_doc(self, docid):
        self.unregs.append(docid)

class Stub(Location):
    pass


class TestEventSubscribers(unittest.TestCase):

    def setUp(self):
        self.root = placefulSetUp(True)
        sm = self.root.getSiteManager()
        self.utility = addUtility(sm, '', IIntIds, IntIdsStub())
        self.cat = addUtility(sm, '', ICatalog, CatalogStub())
        setSite(self.root)

    def tearDown(self):
        placefulTearDown()

    def test_indexDocSubscriber(self):
        from zope.catalog.catalog import indexDocSubscriber
        from zope.container.contained import ObjectAddedEvent
        from zope.intid.interfaces import IntIdAddedEvent

        ob = Stub()
        ob2 = Stub()

        self.root['ob'] = ob
        self.root['ob2'] = ob2

        id = self.utility.register(ob)
        indexDocSubscriber(IntIdAddedEvent(ob, ObjectAddedEvent(ob2)))

        self.assertEqual(self.cat.regs, [(id, ob)])
        self.assertEqual(self.cat.unregs, [])

    def test_reindexDocSubscriber(self):
        from zope.catalog.catalog import reindexDocSubscriber
        from zope.lifecycleevent import ObjectModifiedEvent

        ob = Stub()
        self.root['ob'] = ob

        id = self.utility.register(ob)

        reindexDocSubscriber(ObjectModifiedEvent(ob))

        self.assertEqual(self.cat.regs, [(1, ob)])
        self.assertEqual(self.cat.unregs, [])

        ob2 = Stub()
        self.root['ob2'] = ob2

        reindexDocSubscriber(ObjectModifiedEvent(ob2))
        self.assertEqual(self.cat.regs, [(1, ob)])
        self.assertEqual(self.cat.unregs, [])


    def test_unindexDocSubscriber(self):
        from zope.catalog.catalog import unindexDocSubscriber
        from zope.container.contained import ObjectRemovedEvent
        from zope.intid.interfaces import IntIdRemovedEvent

        ob = Stub()
        ob2 = Stub()
        ob3 = Stub()
        self.root['ob'] = ob
        self.root['ob2'] = ob2
        self.root['ob3'] = ob3

        id = self.utility.register(ob)

        unindexDocSubscriber(
            IntIdRemovedEvent(ob2, ObjectRemovedEvent(ob3)))
        self.assertEqual(self.cat.unregs, [])
        self.assertEqual(self.cat.regs, [])

        unindexDocSubscriber(
            IntIdRemovedEvent(ob, ObjectRemovedEvent(ob3)))
        self.assertEqual(self.cat.unregs, [id])
        self.assertEqual(self.cat.regs, [])


class TestIndexUpdating(unittest.TestCase) :
    """Issue #466: When reindexing a catalog it takes all objects from
    the nearest IntId utility. This is a problem when IntId utility
    lives in another site than the one.

    To solve this issue we simply check whether the objects are living
    within the nearest site.
    """

    def setUp(self):
        placefulSetUp(True)

        from zope.catalog.catalog import Catalog

        self.root = buildSampleFolderTree()

        subfolder = self.root[u'folder1'][u'folder1_1']
        root_sm = self.root_sm = createSiteManager(self.root)
        local_sm = self.local_sm = createSiteManager(subfolder)
        self.utility = addUtility(root_sm, '', IIntIds, IntIdsStub())
        self.cat = addUtility(local_sm, '', ICatalog, Catalog())
        self.cat['name'] = StubIndex('__name__', None)

        for obj in self.iterAll(self.root) :
            self.utility.register(obj)

    def tearDown(self):
        placefulTearDown()

    def iterAll(self, container) :
        from zope.container.interfaces import IContainer
        for value in container.values() :
            yield value
            if IContainer.providedBy(value) :
                for obj in self.iterAll(value) :
                    yield obj

    def test_visitSublocations(self) :
        """ Test the iterContained method which should return only the
        sublocations which are registered by the IntIds.
        """

        names = sorted([ob.__name__ for i, ob in self.cat._visitSublocations()])
        self.assertEqual(names, [u'folder1_1', u'folder1_1_1', u'folder1_1_2'])

    def test_updateIndex(self):
        """ Setup a catalog deeper within the containment hierarchy
        and call the updateIndexes method. The indexed objects should should
        be restricted to the sublocations.
        """
        self.cat.updateIndexes()
        index = self.cat['name']
        names = sorted([ob.__name__ for i, ob in index.doc.items()])
        self.assertEqual(names, [u'folder1_1', u'folder1_1_1', u'folder1_1_2'])

    def test_optimizedUpdateIndex(self):
        """ Setup a catalog deeper within the containment hierarchy together
        with its intid utility. The catalog will not visit sublocations
        because the intid utility can not contain objects outside the site
        where it is registered.
        """
        utility = addUtility(self.local_sm, '', IIntIds, IntIdsStub())
        subfolder = self.root[u'folder1'][u'folder1_1']
        for obj in self.iterAll(subfolder) :
            utility.register(obj)

        self.cat.updateIndexes()
        index = self.cat['name']
        names = sorted([ob.__name__ for i, ob in index.doc.items()])
        self.assertEqual(names, [u'folder1_1_1', u'folder1_1_2'])


class TestSubSiteCatalog(unittest.TestCase) :
    """If a catalog is defined in a sub site and the hooks.setSite was
    not set the catalog will not be found unless the context in
    getAllUtilitiesRegisteredFor is set.
    """

    def setUp(self):
        placefulSetUp(True)

        from zope.catalog.catalog import Catalog

        self.root = buildSampleFolderTree()

        self.subfolder = self.root[u'folder1'][u'folder1_1']
        root_sm = self.root_sm = createSiteManager(self.root)
        local_sm = self.local_sm = createSiteManager(self.subfolder)
        self.utility = addUtility(root_sm, '', IIntIds, IntIdsStub())
        self.cat = addUtility(local_sm, '', ICatalog, Catalog())
        self.cat['name'] = StubIndex('__name__', None)

        for obj in self.iterAll(self.root) :
            self.utility.register(obj)


    def tearDown(self):
        placefulTearDown()

    def iterAll(self, container) :
        from zope.container.interfaces import IContainer
        for value in container.values() :
            yield value
            if IContainer.providedBy(value) :
                for obj in self.iterAll(value) :
                    yield obj



    def test_Index(self):
        """ Setup a catalog deeper within the containment hierarchy
        and call the updateIndexes method. The indexed objects should should
        be restricted to the sublocations.
        """
        from zope.catalog.catalog import indexDocSubscriber
        from zope.container.contained import ObjectAddedEvent

        ob = Stub()
        self.subfolder['ob'] = ob

        id = self.utility.register(ob)

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 0)

        setSite(None)
        indexDocSubscriber(ObjectAddedEvent(ob))

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 1)


    def test_updateIndex(self):
        """ Setup a catalog deeper within the containment hierarchy
        and call the updateIndexes method. The indexed objects should should
        be restricted to the sublocations.
        """
        from zope.catalog.catalog import reindexDocSubscriber
        from zope.lifecycleevent import ObjectModifiedEvent

        ob = Stub()
        self.subfolder['ob'] = ob

        id = self.utility.register(ob)

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 0)

        setSite(None)
        reindexDocSubscriber(ObjectModifiedEvent(ob))

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 1)

    def test_UnIndex(self):
        """ Setup a catalog deeper within the containment hierarchy
        and call the updateIndexes method. The indexed objects should should
        be restricted to the sublocations.
        """
        from zope.catalog.catalog import indexDocSubscriber
        from zope.catalog.catalog import unindexDocSubscriber
        from zope.container.contained import ObjectAddedEvent
        from zope.container.contained import ObjectRemovedEvent

        ob = Stub()
        self.subfolder['ob'] = ob

        id = self.utility.register(ob)

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 0)

        setSite(None)
        indexDocSubscriber(ObjectAddedEvent(ob))

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 1)

        setSite(None)
        unindexDocSubscriber(ObjectRemovedEvent(ob))

        setSite(self.subfolder)
        res = self.cat.searchResults(name='ob')
        self.assertEqual(len(res), 0)


class TestCatalogBugs(PlacelessSetup, unittest.TestCase):
    """I found that z.a.catalog, AttributeIndex failed to remove the previous
    value/object from the index IF the NEW value is None.
    """

    def test_updateIndexWithNone(self):
        uidutil = IntIdsStub()
        provideUtility(uidutil, IIntIds)

        catalog = Catalog()
        index = FieldIndex('author', None)
        catalog['author'] = index

        ob1 = stoopid(author = "joe")
        ob1id = uidutil.register(ob1)
        catalog.index_doc(ob1id, ob1)

        res = catalog.searchResults(author=('joe','joe'))
        names = [x.author for x in res]
        names.sort()
        self.assertEqual(len(names), 1)
        self.assertEqual(names, ['joe'])

        ob1.author = None
        catalog.index_doc(ob1id, ob1)

        #the index must be empty now because None values are never indexed
        res = catalog.searchResults(author=(None, None))
        self.assertEqual(len(res), 0)

    def test_updateIndexFromCallableWithNone(self):
        uidutil = IntIdsStub()
        provideUtility(uidutil, IIntIds)

        catalog = Catalog()
        index = FieldIndex('getAuthor', None, field_callable=True)
        catalog['author'] = index

        ob1 = stoopidCallable(author = "joe")

        ob1id = uidutil.register(ob1)
        catalog.index_doc(ob1id, ob1)

        res = catalog.searchResults(author=('joe','joe'))
        names = [x.author for x in res]
        names.sort()
        self.assertEqual(len(names), 1)
        self.assertEqual(names, ['joe'])

        ob1.author = None
        catalog.index_doc(ob1id, ob1)

        #the index must be empty now because None values are never indexed
        res = catalog.searchResults(author=(None, None))
        self.assertEqual(len(res), 0)

class stoopidCallable(object):
    def __init__(self, **kw):
        #leave the door open to not to set self.author
        self.__dict__.update(kw)

    def getAuthor(self):
        return self.author

class TestIndexRaisingValueGetter(PlacelessSetup, unittest.TestCase):
    """ """
    def test_IndexRaisingValueGetter(self):
        """We can have indexes whose values are determined by callable
        methods.
        Raising an exception in the method should not be silently ignored
        That would cause index corruption -- the index would be out of sync"""
        uidutil = IntIdsStub()
        provideUtility(uidutil, IIntIds)

        catalog = Catalog()
        index = FieldIndex('getAuthor', None, field_callable=True)
        catalog['author'] = index

        ob1 = stoopidCallable(author = "joe")
        ob1id = uidutil.register(ob1)
        catalog.index_doc(ob1id, ob1)

        res = catalog.searchResults(author=('joe','joe'))
        names = [x.author for x in res]
        names.sort()
        self.assertEqual(len(names), 1)
        self.assertEqual(names, ['joe'])

        ob2 = stoopidCallable() # no author here, will raise AttributeError
        ob2id = uidutil.register(ob2)
        try:
            catalog.index_doc(ob2id, ob2)
            self.fail("AttributeError exception should be raised")
        except AttributeError:
            #this is OK, we WANT to have the exception
            pass


#------------------------------------------------------------------------
# placeful setUp/tearDown
def placefulSetUp(site=False):
    testing.setUp()
    eventtesting.setUp()
    traversingSetUp()
    setHooks()
    provideAdapter(ContainerTraversable,
                   (ISimpleReadContainer,), ITraversable)
    provideAdapter(SiteManagerAdapter, (Interface,), IComponentLookup)

    if site:
        root = rootFolder()
        createSiteManager(root, setsite=True)
        return root

def placefulTearDown():
    resetHooks()
    setSite()
    testing.tearDown()


#------------------------------------------------------------------------
# placeless setUp/tearDown
ps = PlacelessSetup()
placelessSetUp = ps.setUp

def placelessTearDown():
    tearDown_ = ps.tearDown
    def tearDown(doctesttest=None):
        tearDown_()
    return tearDown

placelessTearDown = placelessTearDown()
del ps


#------------------------------------------------------------------------
# setup site manager
def createSiteManager(folder, setsite=False):
    if not ISite.providedBy(folder):
        folder.setSiteManager(LocalSiteManager(folder))
    if setsite:
        setSite(folder)
    return api.traverse(folder, "++etc++site")


#------------------------------------------------------------------------
# Local Utility Addition
def addUtility(sitemanager, name, iface, utility, suffix=''):
    """Add a utility to a site manager

    This helper function is useful for tests that need to set up utilities.
    """
    folder_name = (name or (iface.__name__ + 'Utility')) + suffix
    default = sitemanager['default']
    default[folder_name] = utility
    utility = default[folder_name]
    sitemanager.registerUtility(utility, iface, name)
    return utility


#------------------------------------------------------------------------
# Sample Folder Creation
def buildSampleFolderTree():
    # set up a reasonably complex folder structure
    #
    #     ____________ rootFolder ______________________________
    #    /                                    \                 \
    # folder1 __________________            folder2           folder3
    #   |                       \             |                 |
    # folder1_1 ____           folder1_2    folder2_1         folder3_1
    #   |           \            |            |
    # folder1_1_1 folder1_1_2  folder1_2_1  folder2_1_1

    root = rootFolder()
    root[u'folder1'] = Folder()
    root[u'folder1'][u'folder1_1'] = Folder()
    root[u'folder1'][u'folder1_1'][u'folder1_1_1'] = Folder()
    root[u'folder1'][u'folder1_1'][u'folder1_1_2'] = Folder()
    root[u'folder1'][u'folder1_2'] = Folder()
    root[u'folder1'][u'folder1_2'][u'folder1_2_1'] = Folder()
    root[u'folder2'] = Folder()
    root[u'folder2'][u'folder2_1'] = Folder()
    root[u'folder2'][u'folder2_1'][u'folder2_1_1'] = Folder()
    root[u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER A}"
         u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER KA}"
         u"\N{CYRILLIC SMALL LETTER A}3"] = Folder()
    root[u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER A}"
         u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER KA}"
         u"\N{CYRILLIC SMALL LETTER A}3"][
         u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER A}"
         u"\N{CYRILLIC SMALL LETTER PE}"
         u"\N{CYRILLIC SMALL LETTER KA}"
         u"\N{CYRILLIC SMALL LETTER A}3_1"] = Folder()

    return root


def setUp(test):
    root = placefulSetUp(True)
    test.globs['root'] = root


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    suite.addTest(unittest.makeSuite(TestEventSubscribers))
    suite.addTest(unittest.makeSuite(TestIndexUpdating))
    suite.addTest(unittest.makeSuite(TestSubSiteCatalog))
    suite.addTest(unittest.makeSuite(TestCatalogBugs))
    suite.addTest(unittest.makeSuite(TestIndexRaisingValueGetter))
    suite.addTest(doctest.DocTestSuite('zope.catalog.attribute'))
    suite.addTest(doctest.DocFileSuite(
        'README.txt',
        setUp=placelessSetUp,
        tearDown=placelessTearDown,
        ))
    suite.addTest(doctest.DocFileSuite(
        'event.txt',
        setUp=setUp,
        tearDown=lambda x: placefulTearDown(),
        optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
        ))

    return suite


if __name__ == "__main__":
    unittest.main()
