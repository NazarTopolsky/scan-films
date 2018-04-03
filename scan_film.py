# -*- coding: utf-8 -*-
"""
Count times a phrase has been said on some show.
Uses data from http://springfieldspringfield.co.uk/
For now, only supports Python2
Requirements:
  - bs4 (BeautifulSoup)
  - concurrent.futures (backport)
Usage:
python scan_film.py <series> <regex> <threads>
<series> - name of the series as it appears on springfieldspringfield
<regex> - regex to match
<threads> (optional) - number of threads to run downloading process
(only works with concurrent.futures)
"""
import re
import sys
import time
import urlparse
from bs4 import BeautifulSoup
from httplib2 import Http, ServerNotFoundError
try:
    from concurrent.futures import ThreadPoolExecutor
except ImportError:
    ThreadPoolExecutor = None


SITE = 'http://www.springfieldspringfield.co.uk/'
URL = urlparse.urljoin(SITE, 'episode_scripts.php')

BR_REGEX = re.compile('<br\s?/?>', re.MULTILINE)
TOTAL_BYTES = 0


class HttpError(Exception):
    pass


def concurrent_sum(func, _iterable, max_threads=10):
    """Run sum in parallel if concurrent.futures is installed,
    just plain sum otherwise"""
    if ThreadPoolExecutor:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            return sum(executor.map(func, _iterable))
    else:
        return sum([func(x) for x in _iterable])


def is_absolute_url(url):
    return bool(urlparse.urlparse(url).netloc)


def get_episode_links(show_title):
    """Extract links to all episodes of the give show"""
    url = URL + '?tv-show=' + show_title
    http = Http()
    status, response = http.request(url)
    global TOTAL_BYTES
    TOTAL_BYTES += int(status.get('content-length', 0))
    if int(status['status']) >= 400:
        raise HttpError
    links = []
    regex = re.compile('s\d+e\d+')
    for a in BeautifulSoup(response, 'lxml').findAll('a'):
        if a.has_attr('href'):
            link = a['href']
            if regex.search(link):
                if not is_absolute_url(link):
                    link = urlparse.urljoin(SITE, link)
                links.append(link)
    return links


def get_episode_script(link):
    """Get episode script using given link"""
    http = Http()
    status, response = http.request(link)
    global TOTAL_BYTES
    TOTAL_BYTES += int(status.get('content-length', 0))
    return BeautifulSoup(response, 'lxml').find(
        'div',
        attrs={'class': 'scrolling-script-container'}
    )


def count_occurrences(args):
    """Download an episode script using given link and count how much
    times does regex yield a match"""
    try:
        link, regex = args[0], args[1]
    except IndexError:
        n = len(args)
        raise TypeError("count_occurrences() takes exactly 2 arguments "
                        "({} given)".format(n))
    script = unicode(get_episode_script(link))
    # strip '<div class="episode_script"></div>'
    script = script.replace('<div class="episode_script">', '', 1)
    script = script.rsplit('</div>', 1)[0]
    # strip all <br> tags
    script = BR_REGEX.sub(' ', script)
    return len(regex.findall(script))


def main(show_title, phrase_regex, thread_count):
    regex = re.compile(phrase_regex, re.IGNORECASE | re.MULTILINE)
    _title = '-'.join(show_title.lower().split())
    try:
        links = get_episode_links(_title)
    except HttpError:
        print('Show with given title was not found')
        return
    episode_count = len(links)
    occurrences = concurrent_sum(func=count_occurrences,
                                 _iterable=((x, regex) for x in links),
                                 max_threads=thread_count)
    print(
        '"{0}" was mentioned {1} time(s) in show "{2}" ({3} episodes)'.format(
            phrase_regex, occurrences, show_title, episode_count
        )
    )
    if occurrences:
        print('{:0.2f} times per episode'.format(
            occurrences / float(episode_count)
        ))


if __name__ == '__main__':
    try:
        start = time.time()
        try:
            threads = int(sys.argv[3])
        except (IndexError, ValueError):
            threads = 10
        main(sys.argv[1], sys.argv[2], threads)
        print('Elapsed {:0.4f} s, downloaded {} bytes'.format(
            time.time() - start, TOTAL_BYTES
        ))
    except IndexError:
        print('{} requires show title and phrase as parameters'.format(
            sys.argv[0]
        ))
        sys.exit(2)
    except ServerNotFoundError:
        print('Could not reach server (check your internet connection).')
