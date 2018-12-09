#!/usr/bin/env python

import feedparser
import feedgenerator
import ftr

from urllib.parse import urlparse


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


class abstract_modder(object):
    def mod(self, rss_entry, url):
        """
            Returns a tuple with the to update fields

        """
        raise NotImplementedError("Override this method!")

    def update_entry(self, entry):
        update = self.mod(entry, entry.link)
        for name, value in update.items():
            if name == 'content':
                assert len(entry.content) == 1
                entry.content[0].value = value
                entry.content[0].type = 'application/xhtml+xml'
        return entry


class ftr_modder(abstract_modder):
    def mod(self, rss, url):
        extractor = ftr.process(url)

        return {"content": extractor.body}


feeds = {
    "https://www.heise.de/newsticker/heise-atom.xml":
        [(~ link_contains('techstage.de')) & (~ link_contains('heise.de/tr')),
         ftr_modder()]
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

        if (isinstance(fil, abstract_filter) or
                isinstance(fil, abstract_modder)):
            fil = [fil]

        if (not isinstance(fil, list)):
            raise Exception("Wrong type of filter / modder")

        new_entries = [e for e in f.entries]
        for fsub in fil:
            if isinstance(fsub, abstract_filter):
                new_entries = [e for e in new_entries if fsub.match(e)]
            elif isinstance(fsub, abstract_modder):
                new_entries = [fsub.update_entry(e)
                               for e in new_entries]

        f['entries'] = new_entries
        out = generate_feed(f)

        parsed_uri = urlparse(feed)

        open(f'out/{parsed_uri.netloc.replace(".", "_")}.rss', 'w').write(out)


if __name__ == '__main__':
    main()
