"""Define functions to process ISBNs and OCLC numbers."""

# from collections import defaultdict
from logging import getLogger
from threading import Thread
from typing import Optional

from langid import classify
from regex import compile as regex_compile, DOTALL

from config import LANG
from lib.ketabir import url2dictionary as ketabir_url2dictionary
from lib.ketabir import isbn2url as ketabir_isbn2url
from lib.bibtex import parse as bibtex_parse
from lib.commons import dict_to_sfn_cit_ref, request, ISBN13_SEARCH, \
    ISBN10_SEARCH
from lib.ris import ris_parse


OTTOBIB_SEARCH = regex_compile(
    '<textarea[^>]*+>(.*?)</textarea>',
    DOTALL,
).search

RM_DASH_SPACE = str.maketrans('', '', '- ')


class IsbnError(Exception):

    """Raise when bibliographic information is not available."""

    pass


def isbn_scr(
    isbn_container_str: str, pure: bool = False, date_format: str = '%Y-%m-%d'
) -> tuple:
    """Create the response namedtuple."""
    if pure:
        isbn = isbn_container_str
    else:
        # search for isbn13
        m = ISBN13_SEARCH(isbn_container_str)
        if m is not None:
            isbn = m[0]
        else:
            # search for isbn10
            m = ISBN10_SEARCH(isbn_container_str)
            isbn = m[0]

    ketabir_result_list = []
    ketabir_thread = Thread(
        target=ketabir_thread_target,
        args=(isbn, ketabir_result_list))
    ketabir_thread.start()

    citoid_result_list = []
    citoid_thread = Thread(
        target=citoid_thread_target,
        args=(isbn, citoid_result_list))
    citoid_thread.start()

    ottobib_bibtex = ottobib(isbn)
    if ottobib_bibtex:
        otto_dict = bibtex_parse(ottobib_bibtex)
    else:
        otto_dict = None

    ketabir_thread.join()
    if ketabir_result_list:
        ketabir_dict = ketabir_result_list[0]
    else:
        ketabir_dict = None
    dictionary = choose_dict(ketabir_dict, otto_dict)

    citoid_thread.join()
    if citoid_result_list:
        dictionary['oclc'] = citoid_result_list[0]['oclc']

    dictionary['date_format'] = date_format
    if 'language' not in dictionary:
        dictionary['language'] = classify(dictionary['title'])[0]
    return dict_to_sfn_cit_ref(dictionary)


def ketabir_thread_target(isbn: str, result: list) -> None:
    # noinspection PyBroadException
    try:
        url = ketabir_isbn2url(isbn)
        if url is None:  # ketab.ir does not have any entries for this isbn
            return
        d = ketabir_url2dictionary(url)
        if d:
            result.append(d)
    except Exception:
        logger.exception('isbn: %s', isbn)
        return


def choose_dict(ketabir_dict, otto_dict):
    """Choose which source to use.

    Return ketabir_dict if both dicts are available and lang is fa.
    Return otto_dict if both dicts are available and lang is not fa.
    Return ketabir_dict if ketabir_dict is None.
    Return otto_dict otherwise.
    """
    if not otto_dict and not ketabir_dict:
        raise IsbnError('Bibliographic information not found.')
    if ketabir_dict and otto_dict:
        # both exist
        if LANG == 'fa':
            return ketabir_dict
        return otto_dict
    if ketabir_dict:
        return ketabir_dict  # only ketabir exists
    return otto_dict  # only ottobib exists


def isbn2int(isbn):
    return int(isbn.translate(RM_DASH_SPACE))


def get_citoid_dict(isbn) -> Optional[dict]:
    # https://www.mediawiki.org/wiki/Citoid/API
    r = request(
        'https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/' + isbn)
    if r.status_code != 200:
        return
    return r.json()[0]
    # Currently get_citoid_dict is only used to get oclc id (T160845)
    # j0 = r.json()[0]
    # d = defaultdict(lambda: None, j0)
    # d['cite_type'] = j0['itemType']
    # d['isbn'] = d['ISBN'][0]
    # if 'date' in j0:
    #     d['year'] = j0['date']
    # if 'author' in j0:
    #     d['authors'] = [
    #         Name(first.rstrip('.,'), last.rstrip('.,'))
    #         for last, first in j0['author']
    #     ]
    # if 'url' in j0:
    #     del d['url']
    # if 'place' in j0:
    #     d['publisher-location'] = j0['place']
    # return d


def citoid_thread_target(isbn: str, result: list) -> None:
    citoid_dict = get_citoid_dict(isbn)
    if citoid_dict:
        result.append(citoid_dict)


def ottobib(isbn):
    """Convert ISBN to bibtex using ottobib.com."""
    m = OTTOBIB_SEARCH(request(
        'http://www.ottobib.com/isbn/' + isbn + '/bibtex').content.decode())
    if m is not None:
        return m[1]


def oclc_scr(oclc: str, date_format: str = '%Y-%m-%d') -> tuple:
    text = request(
        'https://www.worldcat.org/oclc/' + oclc + '?page=endnote'
        '&client=worldcat.org-detailed_record').content.decode()
    if '<html' in text:  # invalid OCLC number
        return (
            'Error processing OCLC number: ' + oclc,
            'Perhaps you entered an invalid OCLC number?',
            '')
    d = ris_parse(text)
    authors = d['authors']
    if authors:
        # worldcat has a '.' the end of the first name
        d['authors'] = [(
            fn.rstrip('.') if not fn.isupper() else fn,
            ln.rstrip('.') if not ln.isupper() else ln,
        ) for fn, ln in authors]
    d['date_format'] = date_format
    d['oclc'] = oclc
    d['title'] = d['title'].rstrip('.')
    return dict_to_sfn_cit_ref(d)


logger = getLogger(__name__)
