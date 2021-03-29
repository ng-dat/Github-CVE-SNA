import logging
from datetime import datetime


class Logger:

    def __init__(self, filename="logs/log.txt"):
        logging.basicConfig(filename=filename, level=logging.INFO, format='%(message)s')
        self.log(str(datetime.now()))

    def log(self, content):
        print(content)
        logging.info(content)


logger = Logger()