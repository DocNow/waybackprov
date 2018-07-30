#!/usr/bin/env python3

import re
import csv
import sys
import json
import time
import codecs
import logging
import operator
import datetime
import optparse
import collections

from functools import reduce
from urllib.parse import quote
from urllib.request import urlopen

colls = {}

def main():
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
    parser.add_option('--match', help='limit to urls that match pattern')
    parser.add_option('--log', help='where to log activity to')
    opts, args = parser.parse_args()

    if opts.log:
        logging.basicConfig(
            filename=opts.log,
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
    else:
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.WARN
        )
    if len(args) != 1:
        parser.error('You must supply a URL to lookup')

    url = args[0]

    crawl_data = get_crawls(url, 
        start_year=opts.start,
        end_year=opts.end, 
        collapse=opts.collapse, 
        prefix=opts.prefix,
        match=opts.match
    )

    if opts.format == 'text':
        crawls = 0
        coll_urls = {}
        coll_counter = collections.Counter()
        for crawl in crawl_data:
            crawls += 1
            coll_counter.update(crawl['collections'])
            for coll in crawl['collections']:
                # keep track of urls in each collection
                if coll not in coll_urls:
                    coll_urls[coll] = set()
                coll_urls[coll].add(crawl['url'])

        if len(coll_counter) == 0:
            return 

        max_pos = str(len(str(coll_counter.most_common(1)[0][1])))
        if opts.prefix:
            str_format = '%' + max_pos + 'i %' + max_pos + 'i https://archive.org/details/%s'
        else:
            str_format = '%' + max_pos + 'i https://archive.org/details/%s'

        for coll_id, count in coll_counter.most_common():
            if opts.prefix:
                print(str_format % (count, len(coll_urls[coll_id]), coll_id))
            else:
                print(str_format % (count, coll_id))

        print('')
        print('total crawls: %s' % crawls)
        if (opts.prefix):
            total_urls = len(reduce(operator.or_, coll_urls.values()))
            print('total urls: %s' % total_urls)

    elif opts.format == 'json':
        data = list(crawl_data)
        print(json.dumps(data, indent=2))

    elif opts.format == 'csv':
        w = csv.DictWriter(sys.stdout, 
            fieldnames=['timestamp', 'status', 'collections', 'url', 'wayback_url'])
        for crawl in crawl_data:
            crawl['collections'] = ','.join(crawl['collections'])
            w.writerow(crawl)

def get_crawls(url, start_year=None, end_year=None, collapse=False, 
               prefix=False, match=None):

    if prefix == True:
        for year, sub_url in cdx(url, match=match, start_year=start_year,
                                 end_year=end_year):
            yield from get_crawls(sub_url, start_year=year, end_year=year)
        
    if start_year is None:
        start_year = datetime.datetime.now().year
    else:
        start_year = int(start_year)
    if end_year is None:
        end_year = datetime.datetime.now().year
    else:
        end_year = int(end_year)

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
                            'url': url
                        }
                        c['wayback_url'] = 'https://web.archive.org/web/%s/%s' % (c['timestamp'], url)
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
            reader = codecs.getreader('utf-8')
            return json.load(reader(resp))
        except Exception as e:
            logging.error('caught exception: %s', e)
        logging.info('sleeping for %s seconds', count * 10)
        time.sleep(count * 10)
    raise(Exception("unable to get JSON for %s", url))

def cdx(url, match=None, start_year=None, end_year=None):
    logging.info('searching cdx for %s with regex %s', url, match)

    if match:
        try:
            pattern = re.compile(match)
        except Exception as e:
            sys.exit('invalid regular expression: {}'.format(e))
    else:
        pattern = None

    cdx_url = 'http://web.archive.org/cdx/search/cdx?url={}&matchType=prefix&from={}&to={}'.format(quote(url), start_year, end_year)
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
