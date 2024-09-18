import os
import unittest
import pandas as pd
from typing import Tuple
from pandas.testing import assert_frame_equal


def setup_dirs(fpath) -> Tuple[str, str, str]:
    """
    Args:
        fpath: The file path of the script given by __file__
    """

    indir = fpath[:-3]
    basedir = os.path.dirname(indir)
    outdir = f'{basedir}/outdir'

    os.makedirs(outdir, exist_ok=True)

    return indir, outdir


class TestCase(unittest.TestCase):

    def set_up(self, fpath: str):

        self.indir, self.outdir = setup_dirs(fpath=fpath)


    def assertDataFrameEqual(self, df1: pd.DataFrame, df2: pd.DataFrame):

        assert_frame_equal(df1, df2)

    def assertFileEqual(self, file1: str, file2: str):
        with open(file1) as fh1:
            with open(file2) as fh2:
                self.assertEqual(fh1.read(), fh2.read())