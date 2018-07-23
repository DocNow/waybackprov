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

### Multiple Pages

If you would like to look at all URLs at a particular URL prefix you can use the
--prefix option:

    % waybackprov --prefix https://twitter.com/EPAScottPruitt

This will use the Internet Archive's [CDX
API](https://github.com/webrecorder/pywb/wiki/CDX-Server-API) to also include
URLs that are extensions of the URL you supply, so it would include for example:

    https://twitter.com/EPAScottPruitt/status/1309839080398339

But it can also include things you may not want, such as:

    https://twitter.com/EPAScottPruitt/status/1309839080398339/media/1

To further limit the URLs use the `--match` parameter to specify a regular
expression:

    % waybackprov --prefix --match 'status/\d+$' https://twitter.com/EPAScottPruitt

### Collections

One thing to remember when interpreting this data is that collections can
contain other collections. For example the *edgi_monitor* collection is a
sub-collection of *focused_crawls*.

If you use the `--collapse` option only the most specific collection will be
reported for a given crawl.  So if *coll1* is part of *coll2* which is part of
*coll3*, only *coll1* will be reported instead of *coll1*, *coll2* and *coll3*.
This does involve collection metadata lookups at the Internet Archive API, so it
does slow performance significantly.

### JSON and CSV

If you would rather see the raw data as JSON or CSV use the `--format` option.
When you use either of these formats you will see the metadata for each crawl,
rather than a summary.

### Log

You should see a waybackprov.log that contains information about what is going
on behind the scenes.

## Test

If you would like to test it first install [pytest] and then:

    pytest test.py

[pytest]: https://docs.pytest.org/en/latest/
