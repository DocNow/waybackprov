#!/usr/bin/env python3

"""
Give this script a URL and optionally a --start and --end year and it 
will use an (undocumented) Internet Archive API call to fetch the data
behind the calendar view and summarize which Internet Archive collections
are saving the URL the most.

For example:

% waybackprov https://twitter.com/EPAScottPruitt
364 https://archive.org/details/focused_crawls
306 https://archive.org/details/edgi_monitor
151 https://archive.org/details/www3.epa.gov
 60 https://archive.org/details/epa.gov4
 47 https://archive.org/details/epa.gov5
...

One thing to remember when interpreting this data is that collections 
can contain other collections. For example the edgi_monitor collection
is a subcollection of focused_crawls. If you use the --collapse option
only the most specific collection will be reported for a given crawl.
So if coll1 is part of coll2 which is part of coll3, only coll1 will be reported
instead of coll1, coll2 and coll3. This does involve collection metadata
lookups at the Internet Archive API, so it does slow performance significantly.

If you would rather see the raw data as JSON or CSV use the --format option.
"""

import csv
import sys
import json
import time
import logging
import datetime
import optparse
import collections

from urllib.request import urlopen

colls = {}

def main():
    logging.basicConfig(filename='waybackprov.log', level=logging.INFO)
    now = datetime.datetime.now()

    parser = optparse.OptionParser('waybackprov.py [options] <url>')
    parser.add_option('--start', default=now.year, help='start year')
    parser.add_option('--end', default=now.year, help='end year')
    parser.add_option('--format', choices=['text', 'csv', 'json'], 
                      default='text', help='output data')
    parser.add_option('--collapse', action='store_true', 
                      help='only display most specific collection')
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.error('You must supply a URL to lookup')

    url = args[0]

    crawl_data = get_crawls(url, opts.start, opts.end, opts.collapse)

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

def get_crawls(url, start_year=None, end_year=None, collapse=False):
    if start_year is None:
        start_year = datetime.datetime.now().year
    if end_year is None:
        end_year = datetime.datetime.now().year

    api = 'https://web.archive.org/__wb/calendarcaptures?url=%s&selected_year=%s'
    for year in range(start_year, end_year + 1):
        # This calendar data structure reflects the layout of a calendar
        # month. So some spots in the first and last row are null. Not
        # every day has any data if the URL wasn't crawled then.
        logging.info("getting calendar for %s", year)
        cal = get_json(api % (url, year))
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
                        if collapse and len(c['collections']) > 0:
                            c['collections'] = [deepest_collection(c['collections'])]
                        yield c

def deepest_collection(coll_ids):
    return max(coll_ids, key=get_depth)

def get_collection(coll_id):
    # no need to fetch twice
    if coll_id in colls:
        return colls[coll_id]

    logging.info('fetching collection %s', coll_id)

    # get the collection metadata
    url = 'https://archive.org/metadata/%s' % coll_id
    data = get_json(url)['metadata']

    # make collection into reliable array
    if 'collection' in data:
        if type(data['collection']) == str:
            data['collection'] = [data['collection']]
    else:
        data['collection'] = []

    # so we don't have to look it up again
    colls[coll_id] = data

    return data

def get_depth(coll_id, seen_colls=None):
    coll = get_collection(coll_id)
    if 'depth' in coll:
        return coll['depth']

    logging.info('calculating depth of %s', coll_id)

    if len(coll['collection']) == 0:
        return 0

    # prevent recursive loops
    if seen_colls == None:
        seen_colls = set()
    if coll_id in seen_colls:
        return 0
    seen_colls.add(coll_id)

    depth = max(map(lambda id: get_depth(id, seen_colls) + 1, coll['collection']))

    coll['depth'] = depth
    logging.info('depth %s = %s', coll_id, depth)
    return depth

def get_json(url):
    count = 0
    while True:
        count += 1
        if count >= 10:
            logging.error("giving up on fetching JSON from %s", url)
        try:
            resp = urlopen(url)
            return json.loads(resp.read())
        except Exception as e:
            logging.error('caught exception: %s', e)
        logging.info('sleeping for %s seconds', count * 10)
        time.sleep(count * 10)
    raise(Exception("unable to get JSON for %s", url))

if __name__ == "__main__":
    main()
