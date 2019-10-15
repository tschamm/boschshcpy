from BoschShcPy.base import Base

class Error(Base):
  def __init__(self):
    self.code        = None
    self.description = None
    self.parameter   = None

  def __str__(self):
    return str(dict(code=self.code, description=self.description, parameter=self.parameter))

class ErrorException(Exception):
    def __init__(self, errors):
        self.errors = errors
        message = ' '.join([str(e) for e in self.errors])
        super(ErrorException, self).__init__(message)

class SingleErrorException(Exception):
    def __init__(self, errorMessage):
        super(SingleErrorException, self).__init__(errorMessage)

