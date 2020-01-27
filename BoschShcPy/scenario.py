from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList

class ScenarioList(BaseList):
    def __init__(self):
        # We're expecting items of type Scenario
        super(ScenarioList, self).__init__(Scenario)
        
class Scenario(Base):
    def __init__(self):
        """ Initialize a shc scenario.""" 
        self.id = None
        self.name = None
        self.actions = None
    
    def get_id(self):
        return self.id
    
    def update_from_query(self, query_result):
        if query_result['@type'] == "scenario":
            self.load(query_result)

    def __str__(self):
        return "\n".join([
            'Scenario:',
            '  Id                        : %s' % self.id,
            '  name                      : %s' % self.name,
            '  actions                   : %s' % self.actions,
        ])
    
