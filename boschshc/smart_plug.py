from boschshc.base import Base

class SmartPlug(Base):
  def __init__(self):
    self.type = None
    self.switchState = None
    self.automaticPowerOffTime = None
