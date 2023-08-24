'''
' Common logging utility, writes to system's output channels (stderr).
'
' @file: log_helper.py
' @author: Abdullah Alotaibi
' @date: 25/03/2023
'
'''
import sys
import logging

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Logger(metaclass=Singleton):
  _instance = None

  def instance():
    if not Logger._instance:
      logging.basicConfig(
         stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S'
      )
      Logger._instance = logging.getLogger("main")
    return Logger._instance
