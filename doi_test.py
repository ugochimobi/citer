#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Test doi.py module."""


import unittest

import dummy_requests
import doi
from doi import doi_response
from datetime import date as datetime_date


class DoiTest(unittest.TestCase):

    def test_doi1(self):
        self.assertEqual(
            "* {{cite journal | last=Atkins | first=Joshua H. | "
            "last2=Gershell | first2=Leland J. | title=From the analyst's "
            "couch: Selective anticancer drugs | journal=Nature Reviews Drug "
            "Discovery | publisher=Springer Nature | volume=1 | issue=7 | "
            "year=2002 | issn=1474-1784 | doi=10.1038/nrd842 | pages=491–492 "
            "| ref=harv}}",
            doi_response('https://doi.org/10.1038%2Fnrd842').cite,
        )

    def test_doi2(self):
        """Title of this DOI could not be detected in an older version."""
        self.assertEqual(
            '* {{cite journal | title=Books of Critical Interest '
            '| journal=Critical Inquiry '
            '| publisher=University of Chicago Press | volume=40 '
            '| issue=3 | year=2014 | issn=0093-1896 | doi=10.1086/677379 '
            '| pages=272–281 '
            '| ref={{sfnref | University of Chicago Press | 2014}}'
            '}}',
            doi_response(
                'http://www.jstor.org/stable/info/10.1086/677379'
            ).cite,
        )

    def test_doi3(self):
        """No author. URL contains %2F."""
        self.assertEqual(
            '* {{cite journal | last=Spitzer | first=H. F. '
            '| title=Studies in retention. '
            '| journal=Journal of Educational Psychology '
            '| publisher=American Psychological Association (APA) '
            '| volume=30 | issue=9 | year=1939 | issn=0022-0663 '
            '| doi=10.1037/h0063404 | pages=641–656 '
            '| ref=harv}}',
            doi_response('https://doi.org/10.1037%2Fh0063404').cite,
        )

    def test_doi4(self):
        """publisher=Informa {UK"""
        self.assertEqual(
            '* {{cite journal | last=Davis | first=Margaret I. | last2=Jason '
            '| first2=Leonard A. | last3=Ferrari | first3=Joseph R. '
            '| last4=Olson | first4=Bradley D. | last5=Alvarez '
            '| first5=Josefina '
            '| title=A Collaborative Action Approach to Researching Substance'
            ' Abuse Recovery '
            '| journal=The American Journal of Drug and Alcohol Abuse '
            '| publisher=Informa UK Limited '
            '| volume=31 | issue=4 | year=2005 | issn=0095-2990 '
            '| doi=10.1081/ada-200068110 | pages=537–553 '
            '| ref=harv}}',
            doi_response('10.1081%2Fada-200068110').cite,
        )

    def test_incollection(self):
        """Test the `incollection` type."""
        self.assertEqual(
            '* {{cite book | last=Meyer | first=Albert R. '
            '| title=Lecture Notes in Mathematics '
            '| chapter=Weak monadic second order theory of succesor is not'
            ' elementary-recursive | publisher=Springer Berlin Heidelberg '
            '| year=1975 | isbn=978-3-540-07155-6 | issn=0075-8434 '
            '| doi=10.1007/bfb0064872 '
            '| ref=harv'
            '}}',
            doi_response('DOI 10.1007/BFb0064872').cite
        )

    def test_doi_isbn_no_year(self):
        """Test when issue date is empty.

        Also the ISBN may sometimes be invalid.

        """
        self.maxDiff = None
        self.assertEqual(
            '* {{cite thesis | last=Ambati | first=V.R. '
            '| title=Forecasting water waves and currents :'
            ' a space-time approach '
            '| publisher=University Library/University of Twente '
            '| isbn=978-90-365-2632-6 | doi=10.3990/1.9789036526326 '
            '| ref=harv}}',
            doi_response('10.3990/1.9789036526326').cite
        )


doi.requests_get = dummy_requests.DummyRequests().get
if __name__ == '__main__':
    unittest.main()
