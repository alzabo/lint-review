from __future__ import absolute_import
from os.path import abspath
from lintreview.review import Problems
from lintreview.review import Comment
from lintreview.utils import in_path, bundle_exists
from lintreview.tools.puppetsyntax import PuppetSyntax
from unittest import TestCase
from unittest import skipIf
from nose.tools import eq_
from operator import attrgetter

puppet_missing = not(in_path('puppet') or bundle_exists('puppet'))


class TestPuppetSyntax(TestCase):
    needs_puppet = skipIf(puppet_missing, 'Missing puppet, cannot run')

    fixtures = [
        'tests/fixtures/puppetsyntax/no_errors.pp',
        'tests/fixtures/puppetsyntax/has_errors.pp',
        'tests/fixtures/puppetsyntax/eof_error.pp',
    ]

    def setUp(self):
        self.problems = Problems()
        self.tool = PuppetSyntax(self.problems)

    def test_match_file(self):
        self.assertFalse(self.tool.match_file('test.py'))
        self.assertFalse(self.tool.match_file('dir/name/test.py'))
        self.assertTrue(self.tool.match_file('test.pp'))
        self.assertTrue(self.tool.match_file('dir/name/test.pp'))

    @needs_puppet
    def test_process_files__one_file_pass(self):
        self.tool.process_files([self.fixtures[0]])
        eq_([], self.problems.all(self.fixtures[0]))

    @needs_puppet
    def test_process_files__one_file_fail(self):
        filename = abspath(self.fixtures[1])
        self.tool.process_files([filename])
        expected_problems = [
            Comment(filename, 2, 2,
                    ("Error: Unacceptable name. The name 'bad-name' is "
                     "unacceptable as the name of a Host Class Definition")),
            Comment(filename, 4, 4,
                    ("Error: The parameter 'dupe_param' is declared more "
                     "than once in the parameter list"))]

        problems = sorted(self.problems.all(filename), key=attrgetter('line'))
        eq_(expected_problems, problems)

    @needs_puppet
    def test_process_files__two_files(self):
        self.tool.process_files(self.fixtures)

        bad_syntax_filename = abspath(self.fixtures[1])
        eq_(2, len(self.problems.all(bad_syntax_filename)))

        good_syntax_filename = abspath(self.fixtures[0])
        eq_([], self.problems.all(good_syntax_filename))

    @needs_puppet
    def test_process_files__error_at_eof(self):
        filename = abspath(self.fixtures[2])
        self.tool.process_files([filename])
        expected_problems = [Comment(filename, 0, 0,
                                     'Syntax error at end of file')]
        eq_(expected_problems, self.problems.all(filename))
