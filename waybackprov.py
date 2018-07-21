#!/usr/bin/env python3

import re
import csv
import sys
import json
import time
import codecs
import logging
import datetime
import optparse
import collections

from urllib.parse import quote
from urllib.request import urlopen

colls = {}

def main():
    logging.basicConfig(
        filename='waybackprov.log',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    now = datetime.datetime.now()

    parser = optparse.OptionParser('waybackprov.py [options] <url>')
    parser.add_option('--start', default=now.year, help='start year')
    parser.add_option('--end', default=now.year, help='end year')
    parser.add_option('--format', choices=['text', 'csv', 'json'], 
                      default='text', help='output data')
    parser.add_option('--collapse', action='store_true', 
                      help='only display most specific collection')
    parser.add_option('--prefix', action='store_true',
                      help='use url as a prefix')
    parser.add_option('--regex', help='limit to urls that match pattern')
    opts, args = parser.parse_args()

    if len(args) != 1:
        parser.error('You must supply a URL to lookup')

    url = args[0]

    crawl_data = get_crawls(url, 
        start_year=opts.start,
        end_year=opts.end, 
        collapse=opts.collapse, 
        prefix=opts.prefix,
        regex=opts.regex
    )

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

def get_crawls(url, start_year=None, end_year=None, collapse=False, 
               prefix=False, regex=None):

    if prefix == True:
        for year, sub_url in cdx(url, regex=regex):
            yield from get_crawls(sub_url, start_year=year, end_year=year)
        
    if start_year is None:
        start_year = datetime.datetime.now().year
    if end_year is None:
        end_year = datetime.datetime.now().year

    api = 'https://web.archive.org/__wb/calendarcaptures?url=%s&selected_year=%s'
    for year in range(start_year, end_year + 1):
        # This calendar data structure reflects the layout of a calendar
        # month. So some spots in the first and last row are null. Not
        # every day has any data if the URL wasn't crawled then.
        logging.info("getting calendar year %s for %s", year, url)
        cal = get_json(api % (url, year))
        found = False
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
                        logging.info('found crawl %s', c)
                        found = True
                        yield c
        if not found:
            logging.warn('%s is not archived', url)

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

def cdx(url, regex=None):
    logging.info('searching cdx for %s with regex %s', url, regex)
    try:
        pattern = re.compile(regex)
    except Exception as e:
        sys.exit('invalid regular expression: {}'.format(e))

    cdx_url = 'http://web.archive.org/cdx/search/cdx?url={}&matchType=prefix'.format(quote(url))
    seen = set()
    results = codecs.decode(urlopen(cdx_url).read(), encoding='utf8')

    for line in results.split('\n'):
        parts = line.split(' ')
        if len(parts) == 7:
            year = int(parts[1][0:4])
            url = parts[2]
            seen_key = '{}:{}'.format(year, url)
            if seen_key in seen:
                continue
            if pattern and not pattern.search(url):
                continue 
            seen.add(seen_key)
            logging.info('cdx found %s', url)
            yield(year, url)

if __name__ == "__main__":
    main()
