# If for some reason "import logging" doesn't work or isn't available,
# here's a simple version that accomplishes the basics.

class Logger(object):
  DEBUG = 10
  INFO = 20
  WARNING = 30
  ERROR = 40
  FATAL = 50
  LEVELS = {"DEBUG": DEBUG,
            "INFO": INFO,
            "WARNING": WARNING,
            "ERROR": ERROR,
            "FATAL": FATAL}
  
  def __init__(self, level=INFO):
    self.level = self.get_level_num(level)

  @classmethod
  def get_level_num(cls, level):
    try:
      return cls.LEVELS[level]
    except KeyError:
      pass
    if any(v == level for v in cls.LEVELS.itervalues()):
      return level
    raise ValueError("Invalid level: {0}".format(level))

  def log(self, level, string):
    if self.get_level_num(level) >= self.level:
      print string
      return True
    return False

  def debug(self, string): return self.log(self.DEBUG, string)
  def info(self, string): return self.log(self.INFO, string)
  def warning(self, string): return self.log(self.WARNING, string)
  def error(self, string): return self.log(self.ERROR, string)
  def fatal(self, string): return self.log(self.FATAL, string)

LOGGER = Logger(Logger.WARNING)
