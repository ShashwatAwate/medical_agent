import mesa
from mesa.discrete_space import CellAgent,Network
import networkx

from data.generate_data import SyntheticData
import random
import numpy as np
import queue



class HostpitalAgent(mesa.Agent):
    """Hospital that has inventory, usage and requests things if its running low"""

    def __init__(self, model,init_data):
        super().__init__(model)
        

        self.base_usage,self.inventory = init_data
        self.emergency_multipliter = 1.0
        self.days_remaining = {}
        self.emergency = False
        self.emergency_days = 0.0
        self.days_threshold = 3
        self.target_days = 7
        

    def days_supply_remaining(self):
        """Calculates how much a supply should last under expected conditions"""

        for resource,usage in self.base_usage.items():
            expected_daily_usage = usage*self.emergency_multipliter
            self.days_remaining[resource] = self.inventory[resource]/expected_daily_usage

    def request_resources(self):
        """Requests for resource if days of supply becomes less than threshold"""
        
        for resource,remaining in self.days_remaining.items():
            expected_daily_usage = self.base_usage[resource]*self.emergency_multipliter

            if remaining < self.days_threshold:
                request_amt = (self.target_days - remaining)*expected_daily_usage
                self.model.register_request(self.unique_id,resource,request_amt)

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
            if emergency_chance > 0.5:
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

        self.consume_resources()
        self.update_emergency()
        self.days_supply_remaining()
        self.request_resources()


class HospitalModel(mesa.Model):
    def __init__(self,n,seed=None):
        super().__init__(seed=seed)

        self.sd = SyntheticData()
        self.num_agents = n
        self.requests = queue.Queue(maxsize=0)
        self.inital_conditions = [
            self.sd.generate_data() for _ in range(n)
        ]
        
        HostpitalAgent.create_agents(self,n=n,init_data = self.inital_conditions)

    def register_request(self,hospital: int,resource: str,amount: float):
        """Put requests from agents in a queue"""

        self.requests.put({"hospital":hospital,"resource":resource,"amount":amount})
