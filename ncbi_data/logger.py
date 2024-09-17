import logging
import sys


def get_logger(name, level=logging.INFO):
	formatter = logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\n%(message)s\n', datefmt='%Y-%m-%d %H:%M:%S')

	stream = logging.StreamHandler(sys.stdout)
	stream.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(stream)
	logger.propagate = False

	return logger