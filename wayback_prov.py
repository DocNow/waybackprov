#!/usr/bin/env python3

"""
Give this script a URL and optionally a --start and --end year and it 
will use an (undocumented) Internet Archive API call to fetch the data
behind the calendar view and summarize which Internet Archive collections
are saving the URL the most.

For example:

./wayback-prov.py https://twitter.com/EPAScottPruitt
364 https://archive.org/details/focused_crawls
306 https://archive.org/details/edgi_monitor
151 https://archive.org/details/www3.epa.gov
 60 https://archive.org/details/epa.gov4
 47 https://archive.org/details/epa.gov5
...

If you would rather see the raw data as JSON or CSV use the --format option.

One thing to remember when interpreting this data is that collections 
can contain other collections. For example the edgi_monitor collection
is a subcollection of focused_crawls.

"""

import csv
import sys
import json
import datetime
import optparse
import collections

from urllib.request import urlopen

colls = {}

def main():
    now = datetime.datetime.now()

    parser = optparse.OptionParser('waybackprov.py [options] <url>')
    parser.add_option('--start', default=now.year, help='start year')
    parser.add_option('--end', default=now.year, help='end year')
    parser.add_option('--format', choices=['text', 'csv', 'json'], 
                      default='text', help='output data')
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.error('You must supply a URL to lookup')

    url = args[0]

    crawl_data = get_crawls(url, opts.start, opts.end)

    if opts.format == 'text':
        coll_counter = collections.Counter()
        for crawl in crawl_data:
            coll_counter.update(crawl['collections'])

        max_pos = str(len(str(coll_counter.most_common(1)[0][1])))
        str_format = '%' + max_pos + 'i https://archive.org/details/%s'
        for coll_id, count in coll_counter.most_common():
            print(str_format % (count, coll_id))

    elif opts.format == 'json':
        data = list(crawl_data)
        print(json.dumps(data, indent=2))

    elif opts.format == 'csv':
        w = csv.DictWriter(sys.stdout, 
            fieldnames=['timestamp', 'status', 'collections', 'url'])
        for crawl in crawl_data:
            crawl['collections'] = ','.join(crawl['collections'])
            w.writerow(crawl)

def get_crawls(url, start_year, end_year, flatten=False):
    api = 'https://web.archive.org/__wb/calendarcaptures?url=%s&selected_year=%s'
    for year in range(start_year, end_year + 1):
        # This calendar data structure reflects the layout of a calendar
        # month. So some spots in the first and last row are null. Not
        # every day has any data if the URL wasn't crawled then.
        cal = json.loads(urlopen(api % (url, year)).read())
        for month in cal:
            for week in month:
                for day in week:
                    if day is None or day == {}:
                        continue
                    # note: we can't seem to rely on 'cnt' as a count
                    for i in range(0, len(day['st'])):
                        c = {
                            'status': day['st'][i],
                            'timestamp': day['ts'][i],
                            'collections': day['why'][i],
                        }
                        c['url'] = 'https://web.archive.org/web/%s/%s' % (c['timestamp'], url)
                        if flatten:
                            c['collections'] = flatten_collections(c['collections'])
                        yield c

def flatten_collections(coll_ids):
    # make sure we have all the collections first
    # should be a no-op if we've fetched them before
    for coll_id in coll_ids:
        coll = get_collection(coll_id)
    # now figure out which one is the leaf

def get_collection(coll_id):
    # no need to fetch twice
    if coll_id in colls:
        return colls[coll_id]

    # get the collection metadata
    url = 'https://archive.org/metadata/%s' % coll_id
    data = json.loads(urlopen(url).read())

    # if the collection is part of another collection go get them too
    if 'collection' in data:
        other_colls = data['collection']
        if type(other_colls) == str:
            other_colls = [other_colls]
        # recursively fetch any parent collections
        for other_coll_id in other_colls:
            other_coll = get_collection(other_coll_id)
            other_coll['child_collection'].append(coll_id)

    data['child_collection'] = []
    return data


if __name__ == "__main__":
    main()
