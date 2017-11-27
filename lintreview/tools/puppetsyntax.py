from __future__ import absolute_import
import os
import logging
import re
from lintreview.tools import Tool
from lintreview.tools import run_command
from lintreview.utils import in_path
from lintreview.utils import bundle_exists

log = logging.getLogger(__name__)


class PuppetSyntax(Tool):

    name = 'puppet-syntax'

    def check_dependencies(self):
        """
        See if puppet is on the PATH
        """
        return in_path('puppet') or bundle_exists('puppet')

    def match_file(self, filename):
        base = os.path.basename(filename)
        name, ext = os.path.splitext(base)
        return ext == '.pp'

    def process_files(self, files):
        """
        Run code checks with puppet parser validate
        """
        log.debug('Processing %s files with %s', files, self.name)
        command = ['puppet', 'parser', 'validate']
        if bundle_exists('puppet'):
            command = ['bundle', 'exec', 'puppet', 'parser', 'validate']
        command += ['--color', 'false']
        command += files
        output = run_command(
            command,
            split=True,
            ignore_error=True,
            include_errors=True
        )

        if not output:
            log.debug('No puppet syntax errors found.')
            return False

        for line in output:
            try:
                filename, line, error = self._parse_line(line)
            except AssertionError:
                pass
            else:
                self.problems.add(filename, line, error)

    def _parse_line(self, line):
        """
        `puppet parser validate <file>` lines look like this:
        <severity>:<message> at <filename>:<lineno>:<charno>
        """
        if re.search('Syntax error at end of file', line):
            print line
            filename = line.split()[-1]
            return (filename.strip(), 0, 'Syntax error at end of file')

        parts = line.rsplit(':', 2)

        # some messages that don't correspond to a file line are also
        # emitted
        assert len(parts) == 3

        message, filename = parts[0].rsplit('at', 1)
        return (filename.strip(), int(parts[1]), message.strip())
