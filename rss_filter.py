#!/usr/bin/env python

import feedparser
import feedgenerator

from urllib.parse import urlparse
# from collections import namedtuple


class abstract_filter(object):
    def __or__(self, other):
        class Or(abstract_filter):
            def match(a, entry):
                return self.match(entry) or other.match(entry)
        return Or()

    def __and__(self, other):
        class And(abstract_filter):
            def match(a, entry):
                return self.match(entry) and other.match(entry)
        return And()

    def __invert__(self):
        class Not(abstract_filter):
            def match(a, entry):
                return not self.match(entry)
        return Not()


class link_contains(abstract_filter):
    def __init__(self, part):
        self.part = part

    def match(self, entry):
        return self.part in entry.link


# TODO https://github.com/fivefilters/ftr-site-config
# class content_filler(abstract_modder):
#     pass

feeds = {
    "https://www.heise.de/newsticker/heise-atom.xml":
        (~ link_contains('techstage.de')) & (~ link_contains('heise.de/tr'))
}

def read_feed(url):
    feed = feedparser.parse(url)
    return feed


def generate_feed(f):
    feed = feedgenerator.Rss201rev2Feed(
            title=f.feed.title,
            link=f.feed.link,
            description=f.feed.description
            )

    for e in f.entries:
        feed.add_item(
                title=e.title,
                link=e.link,
                description=e.description)

    return feed.writeString(encoding="UTF8")


def main():
    for feed, fil in feeds.items():
        f = read_feed(feed)

        new_entries = [e for e in f.entries
                       if fil.match(e)]

        f['entries'] = new_entries
        out = generate_feed(f)

        parsed_uri = urlparse(feed)

        open(f'out/{parsed_uri.netloc.replace(".", "_")}.rss', 'w').write(out)


if __name__ == '__main__':
    main()
