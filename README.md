Give *waybackprov* a URL and optionally a `--start` and `--end` year and it will
use an (undocumented) Internet Archive API call to fetch the provenance data
behind the calendar view and summarize which Internet Archive collections are
saving the URL the most.

## Install 

    pip install waybackprov

## Use

So here's how it works:

    % waybackprov https://twitter.com/EPAScottPruitt
    364 https://archive.org/details/focused_crawls
    306 https://archive.org/details/edgi_monitor
    151 https://archive.org/details/www3.epa.gov
     60 https://archive.org/details/epa.gov4
     47 https://archive.org/details/epa.gov5
    ...

One thing to remember when interpreting this data is that collections can
contain other collections. For example the *edgi_monitor* collection is a
sub-collection of *focused_crawls*.

If you use the `--collapse` option only the most specific collection will be
reported for a given crawl.  So if *coll1* is part of *coll2* which is part of
*coll3*, only *coll1* will be reported instead of *coll1*, *coll2* and *coll3*.
This does involve collection metadata lookups at the Internet Archive API, so it
does slow performance significantly.

If you would rather see the raw data as JSON or CSV use the `--format` option.
When you use either of these formats you will see the metadata for each crawl,
rather than a summary.

If you use `--verbose` a log of what waybackprov is doing will be written to
*waybackprov.log*.

## Test

If you would like to test it first install [pytest] and then:

    pytest test.py

[pytest]: https://docs.pytest.org/en/latest/
