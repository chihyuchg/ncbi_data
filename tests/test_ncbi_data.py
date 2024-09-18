import os
import shutil
import unittest
import pandas as pd
from ncbi_data import ncbi_data
from .setup import TestCase


class TestNcbiData(TestCase):

	def setUp(self):
		self.set_up(fpath=__file__)

	def tearDown(self):
		# pass
		shutil.rmtree(self.outdir)

	def test_ncbi_data(self):

		tax_id = '9606'
		download_files = False
		test_assembly_report = ncbi_data.main(taxid=tax_id, download_files=download_files, outdir=self.outdir)
		# ref_assembly_report = f'{self.indir}/ncbi_assembly_report_{tax_id}.csv'

		# self.assertFileEqual(file1=ref_assembly_report, file2=test_assembly_report)


if __name__ == '__main__':
	unittest.main()