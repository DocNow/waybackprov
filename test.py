import pytest
from wayback_prov import *

def test_coll():
    coll = get_collection('ArchiveIt-Collection-2410')
    assert coll['title'] == 'University of Maryland'

def test_get_crawls():
    crawls = list(get_crawls('https://mith.umd.edu'))
    assert len(crawls) > 0
    assert crawls[0]['timestamp']
    assert crawls[0]['url']
    assert crawls[0]['status']
    assert crawls[0]['collections']
    assert len(crawls[0]['collections']) > 0

def test_depth():
    assert get_depth('ArchiveIt-Collection-2410') == 4
    assert get_depth('wikipediaoutlinks00003') == 3

def test_deepest_collection():
    colls = [
        'ArchiveIt-Partner-408',
        'archiveitdigitalcollection',
        'web',
        'archiveitpartners',
        'ArchiveIt-Collection-2410'
    ]
    assert deepest_collection(colls) == 'ArchiveIt-Collection-2410'

