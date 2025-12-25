from mesa.discrete_space import FixedAgent
import random
import numpy as np

class State:
    normal = 0
    emergency = 1
    request = 2

class HostpitalAgent(FixedAgent):
    """Hospital that has inventory, usage and requests things if its running low"""

    def __init__(self, model,cell,usage,inventory,init_state):
        super().__init__(model)
        
        self.base_usage = usage
        self.inventory = inventory
        self.emergency_multipliter = 1.0
        self.days_remaining = {}
        self.emergency = False
        self.emergency_days = 0.0
        self.days_threshold = 3
        self.lead_time = 2
        self.target_days = 7
        self.cell = cell
        self.state = init_state
        # self.id = id
        

    def days_supply_remaining(self):
        """Calculates how much a supply should last under expected conditions"""

        for resource,usage in self.base_usage.items():
            expected_daily_usage = usage*self.emergency_multipliter
            self.days_remaining[resource] = np.ceil(self.inventory[resource]/expected_daily_usage)

    def request_resources(self):
        """Requests for resource if days of supply becomes less than threshold"""
        
        for resource,remaining in self.days_remaining.items():
            expected_daily_usage = self.base_usage[resource]*self.emergency_multipliter
            # print(f"agent num: {self.unique_id} , resource: {resource}, days remaining: {remaining}")
            if remaining < self.days_threshold+self.lead_time and self.model.restock_interval>4:
                request_amt = (self.target_days - remaining)*expected_daily_usage
                self.model.register_request(
                    self.unique_id,
                    resource,
                    request_amt,
                    self.emergency
                    )
                # print(f"INFO: requesting resource {resource} amount: {request_amt}, days left: {remaining}")

    def update_emergency(self):
        """Update Emergency states"""
        if self.emergency:  
            self.emergency_days -=1
            if self.emergency_days <=0:
                self.emergency = False
                self.emergency_multipliter = 1.0
    
    def consume_resources(self):
        """Consume resources daily"""
        if not self.emergency:
            emergency_chance = random.uniform(0.0,1.0)
            if emergency_chance > 0.7:
                self.emergency = True

                self.emergency_multipliter = random.uniform(1.1,1.7)
                self.emergency_days = random.randint(1,6)

        for resource,usage in self.base_usage.items():
            noise = self.random.uniform(0.8,1.2)
            expected_usage = usage*noise*self.emergency_multipliter
            actual_usage = min(expected_usage,self.inventory[resource])
            self.inventory[resource] -= actual_usage
    
    def step(self):
        """One time step in agent"""
        # print(f"INFO: agent step for agent {self.unique_id}")
        self.consume_resources()
        self.update_emergency()
        self.days_supply_remaining()
        self.request_resources()
