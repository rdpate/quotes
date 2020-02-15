import codecs
import glob
import locale
import random
import re
import sys
import textwrap
from collections import namedtuple
from os import path
from pprint import pprint

import yaml

import pyr.optics


Quote = namedtuple("Quote", ["text", "attribution", "ref", "tags", "notes"])

class Options(pyr.optics.OptionAttrs):
    n = None
    grep = None
    show_notes = False
    width = 78
    blank_line = True
    debug = False

def main(opts, args):
    if sys.stdout.encoding is None:
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout, errors="replace")

    opt_map = {
        "n": pyr.optics.nonneg_int,
        "count": "n",
        "grep": pyr.optics.nonempty_string,
        "notes": ("show_notes", pyr.optics.store_true),
        "width": pyr.optics.nonneg_int,
        "no-blank-line": ("blank_line", pyr.optics.store_false),
        "debug": pyr.optics.store_true,
        }
    opts = pyr.optics.parse_opts(opts, opt_map, Options())

    if opts.n is None and opts.grep is None:
        opts.n = 1

    if not args:
        # TODO: better path management
        args = glob.glob(path.join(path.dirname(path.dirname(__file__)), "data", "*.yaml"))

    if opts.debug:
        print("opts:", repr(opts.__dict__))
        print("filenames:", repr(args))

    quotes = []
    for filename in args:
        if opts.debug:
            print("loading", filename)
        collection = path.basename(filename)
        for doc in yaml.load_all(codecs.open(filename, encoding="utf-8", errors="replace")):
            q = doc.get("q")
            if "title" in doc:
                a = doc["title"]
            elif "by" in doc:
                a = doc["by"]
                source = doc.get("source")
                if source:
                    a += ", " + source
            elif "source" in doc:
                a = doc["source"]
            else:
                a = None

            if "ref" in doc:
                ref = doc["ref"]
                if isinstance(ref, list):
                    ref = ", ".join(ref)
            elif "when" in doc:
                ref = str(doc["when"])
            else:
                ref = None

            tags = doc.get("tags", "")

            notes = []
            if "note" in doc:
                notes = doc.get("note")
                if isinstance(notes, str):
                    notes = [notes]
            assert isinstance(notes, list)

            q = Quote(q, a, ref, tags, notes)
            quotes.append((collection, q))

    if opts.debug:
        print("[loaded {} quotes from {} files]".format(len(quotes), len(args)))

    def show_quote(q, collection, is_first):
        if not is_first and opts.blank_line:
            print()

        if opts.debug:
            print("quote =", q)
        text = q.text.strip()
        if opts.width:
            text = textwrap.fill(text, width=opts.width)
        print(text)

        attr = q.attribution
        if q.ref:
            attr = attr or "(unknown)"
            attr += "; " + q.ref

        if attr:
            end_text = "  -- {}".format(attr)
            if opts.show_notes:
                end_text += " [{}]".format(collection)
            print(end_text)
        elif opts.show_notes:
            print("  [{}]".format(collection))

        if opts.show_notes:
            for note in q.notes:
                print("#", note)

    if opts.grep:
        # test if a fixed-string match is possible, could be improved
        if re.escape(opts.grep) == opts.grep:
            opts.grep = opts.grep.lower()
            def grep(s):
                if not isinstance(s, str):
                    return any(grep(x) for x in s)
                return opts.grep in s.lower()
        else:
            def grep(s):
                if not isinstance(s, str):
                    return any(grep(x) for x in s)
                return re.compile(opts.grep, re.I).search(s)
        count = 0
        for collection, q in quotes:
            if any(grep(t) for t in q if t):
                show_quote(q, collection, count == 0)
                count += 1
                if opts.n is not None and count == opts.n:
                    break
    else:
        if not quotes:
            return "no quotes found!"
        for count in range(opts.n):
            collection, q = random.choice(quotes)
            show_quote(q, collection, count == 0)
