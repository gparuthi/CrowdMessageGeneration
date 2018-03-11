from datetime import datetime
import pytz
import os
from pprint import pprint
import sys
from common.dbclient import client, db
import logging

fhandler = logging.FileHandler('./Logs/logfile.log')
formatter = logging.Formatter(
        '%(asctime)s %(name)-4s %(levelname)-8s %(message)s')
fhandler.setFormatter(formatter)
fhandler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# console_format = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)


class logger(object):
    def __init__(self,  logdir='./Logs', fname='common' , insertDate= False, verbose=True, level=logging.DEBUG):
        self.module_name = fname
        self.logr = logging.getLogger(fname)
        self.logr.addHandler(fhandler)
        self.logr.addHandler(console_handler)
        self.logr.setLevel(level)
        if verbose:
            self.debug('inititating logr for %s'%fname)
    """This method is for pretty printing the log 
    """
    def plog(self, log_str, class_name='', data={}):
        self.base_str = '%s | %s' %(class_name, log_str)
        # if client:
        #     try:
        #         rec = {'time':time, 'mudule_name':self.module_name, 'class_name':class_name,
        #             'description':log_str, 'data':data}
        #         db.log.insert(rec)
        #     except:
        #         print 'Problem in pushing to mongodb'
        self.logr.info(self.base_str)

    def debug(self, log_str, class_name='', data={}):
        self.logr.debug(log_str)

    def warning(self, log_str, class_name='', data={}):
        self.logr.warning(log_str)

    def exception(self, log_str, class_name='', data={}):
        self.logr.exception(log_str)

    def error(self, log_str, class_name='', data={}):
        self.logr.error(log_str)