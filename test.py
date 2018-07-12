import pytest
from wayback_prov import *

def test_coll():
    coll = get_collection('ArchiveIt-Collection-2410')
    assert coll['metadata']['title'] == 'University of Maryland'

def test_get_crawls():
    crawls = list(get_crawls('https://mith.umd.edu'))
    assert len(crawls) > 0
    assert crawls[0]['timestamp']
    assert crawls[0]['url']
    assert crawls[0]['status']
    assert crawls[0]['collections']
    assert len(crawls[0]['collections']) > 0

