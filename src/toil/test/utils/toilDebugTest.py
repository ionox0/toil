# Copyright (C) 2018 Regents of the University of California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import absolute_import
# from builtins import str

import unittest
import subprocess
import os
import shutil
import logging
from toil.test import ToilTest, needs_aws, needs_rsync3, integrative, slow
from toil.utils.toilDebugFile import recursiveGlob

logger = logging.getLogger(__name__)

class ToilDebugFileTest(ToilTest):
    """A set of test cases for toilwdl.py"""

    def setUp(self):
        """
        Initial set up of variables for the test.
        """

        subprocess.check_call(['python', os.path.abspath('src/toil/test/utils/ABC/debugWorkflow.py')])
        self.jobStoreDir = os.path.abspath('toilWorkflowRun')
        self.tempDir = self._createTempDir(purpose='tempDir')

    def tearDown(self):
        """Default tearDown for unittest."""

        shutil.rmtree(self.jobStoreDir)

        unittest.TestCase.tearDown(self)

    @slow
    def testJobStoreContents(self):
        """Test toilDebugFile.printContentsOfJobStore().

        Runs a workflow that imports 'B.txt' and 'mkFile.py' into the
        jobStore.  'A.txt', 'C.txt', 'ABC.txt' are then created.  This checks to
        make sure these contents are found in the jobStore and printed."""

        contents = ['A.txt', 'B.txt', 'C.txt', 'ABC.txt', 'mkFile.py']

        subprocess.check_call(['python', os.path.abspath('src/toil/utils/toilDebugFile.py'), self.jobStoreDir, '--listFilesInJobStore=True'])
        jobstoreFileContents = os.path.abspath('jobstore_files.txt')
        files = []
        match = 0
        with open(jobstoreFileContents, 'r') as f:
            for line in f:
                files.append(line.strip())
        for file in files:
            for expected_file in contents:
                if file.endswith(expected_file):
                    match = match + 1
        logger.info(files)
        logger.info(contents)
        logger.info(match)
        # C.txt will match twice (once with 'C.txt', and once with 'ABC.txt')
        assert match == 6

    # expected run time = 4s
    def testFetchJobStoreFiles(self):
        """Test toilDebugFile.fetchJobStoreFiles() without using symlinks."""
        self.fetchFiles(symLink=False)

    # expected run time = 4s
    def testFetchJobStoreFilesWSymlinks(self):
        """Test toilDebugFile.fetchJobStoreFiles() using symlinks."""
        self.fetchFiles(symLink=True)

    def fetchFiles(self, symLink):
        """
        Fn for testFetchJobStoreFiles() and testFetchJobStoreFilesWSymlinks().

        Runs a workflow that imports 'B.txt' and 'mkFile.py' into the
        jobStore.  'A.txt', 'C.txt', 'ABC.txt' are then created.  This test then
        attempts to get a list of these files and copy them over into ./src from
        the jobStore, confirm that they are present, and then delete them.
        """
        contents = ['A.txt', 'B.txt', 'C.txt', 'ABC.txt', 'mkFile.py']
        outputDir = os.path.abspath('src')
        cmd = ['python', os.path.abspath('src/toil/utils/toilDebugFile.py'),
               self.jobStoreDir,
               '--fetch', '*A.txt', '*B.txt', '*C.txt', '*ABC.txt', '*mkFile.py',
               '--localFilePath=' + os.path.abspath('src'),
               '--useSymlinks=' + str(symLink)]
        subprocess.check_call(cmd)
        for file in contents:
            matchingFilesFound = recursiveGlob(outputDir, '*' + file)
            assert len(matchingFilesFound) >= 1, matchingFilesFound
            for fileFound in matchingFilesFound:
                assert fileFound.endswith(file) and os.path.exists(fileFound)
                if fileFound.endswith('-' + file):
                    os.remove(fileFound)