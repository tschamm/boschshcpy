from BoschShcPy.base import Base
from BoschShcPy.base_list import BaseList
from BoschShcPy.error import ErrorException

class ScenarioList(BaseList):
    def __init__(self):
        # We're expecting items of type Scenario
        super(ScenarioList, self).__init__(Scenario)
        
class Scenario(Base):
    def __init__(self):
        """ Initialize a shc scenario.""" 
        self.id = None
        self.client = None
        self.name = None
        self.actions = None
    
    @property
    def get_id(self):
        return self.id
    
    @property
    def get_name(self):
        return self.name

    def set_client(self, client):
        self.client = client
    
    def update_from_query(self, query_result):
        if query_result['@type'] == "scenario":
            self.load(query_result)

    def trigger(self):
        """Trigger a scenario."""
        if self.client:
            try:
                self.client.request("smarthome/scenarios/"+self.id +
                                    "/triggers", method='POST')
                return True
            except ErrorException as e:
                _LOGGER.debug("Request failed with error {}".format(e))
                return False
        return False

    def __str__(self):
        return "\n".join([
            'Scenario:',
            '  Id                        : %s' % self.id,
            '  name                      : %s' % self.name,
            '  actions                   : %s' % self.actions,
        ])
    
