Give *waybackprov* a URL and it will summarize which Internet Archive
collections have archived the URL. This kind of information can sometimes
provide insight about why a particular web resource or set of web resources were
archived from the web.

## Install 

    pip install waybackprov

## Basic Usage

To check a particular URL here's how it works:

    % waybackprov https://twitter.com/EPAScottPruitt
    364 https://archive.org/details/focused_crawls
    306 https://archive.org/details/edgi_monitor
    151 https://archive.org/details/www3.epa.gov
     60 https://archive.org/details/epa.gov4
     47 https://archive.org/details/epa.gov5
    ...

The first column contains the number of crawls for a particular URL, and the
second column contains the URL for the Internet Archive collection that added
it.

## Time

By default waybackprov will only look at the current year. If you would like it
to examine a range of years use the `--start` and `--end` options:

    % waybackprov --start 2016 --end 2018 https://twitter.com/EPAScottPruitt

## Multiple Pages

If you would like to look at all URLs at a particular URL prefix you can use the
`--prefix` option:

    % waybackprov --prefix https://twitter.com/EPAScottPruitt

This will use the Internet Archive's [CDX API](https://github.com/webrecorder/pywb/wiki/CDX-Server-API) to also include URLs that are extensions of the URL you supply, so it would include for example:

    https://twitter.com/EPAScottPruitt/status/1309839080398339

But it can also include things you may not want, such as:

    https://twitter.com/EPAScottPruitt/status/1309839080398339/media/1

To further limit the URLs use the `--match` parameter to specify a regular
expression only check particular URLs. Further specifying the URLs you are
interested in is highly recommended since it prevents lots of lookups for CSS,
JavaScript and image files that are components of the resource that was
initially crawled.

    % waybackprov --prefix --match 'status/\d+$' https://twitter.com/EPAScottPruitt

## Collections

One thing to remember when interpreting this data is that collections can
contain other collections. For example the *edgi_monitor* collection is a
sub-collection of *focused_crawls*.

If you use the `--collapse` option only the most specific collection will be
reported for a given crawl.  So if *coll1* is part of *coll2* which is part of
*coll3*, only *coll1* will be reported instead of *coll1*, *coll2* and *coll3*.
This does involve collection metadata lookups at the Internet Archive API, so it
does slow performance significantly.

## JSON and CSV

If you would rather see the raw data as JSON or CSV use the `--format` option.
When you use either of these formats you will see the metadata for each crawl,
rather than a summary.

## Log

If you would like to see detailed information about what *waybackprov* is doing
use the `--log` option to supply the a file path to log to:

    % waybackprov --log waybackprov.log https://example.com/

## Test

If you would like to test it first install [pytest] and then:

    pytest test.py

[pytest]: https://docs.pytest.org/en/latest/
