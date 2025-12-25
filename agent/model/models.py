import mesa
from mesa.discrete_space import Network,CellCollection
import networkx as nx
from .data.generate_data import SyntheticData
import random
from .agents import HostpitalAgent,State
import numpy as np
import uuid

class HospitalModel(mesa.Model):
    steps=0

    def __init__(self,n=5,seed=None):
        super().__init__(seed=seed)

        self.sd = SyntheticData()
        self.num_agents = n
        
        self.requests = []
        self.pending_transfers = []
        self.hosp_ids = list(range(self.num_agents))
        self.G = nx.Graph()
        self.G.add_nodes_from(self.hosp_ids)
        self.state = State()
        for i in self.hosp_ids:
            for j in self.hosp_ids:
                if i<j:
                    self.G.add_edge(i,j,distance=random.randint(40,400))
        self.space = Network(self.G,capacity=1)
        self.restock_interval = 3
        self.days_threshold = 2
        self.base_stock_pct = 40
        self.min_dist_delay = {
            100: 0,
            200: 0,
            300: 0,
            400: 0
        }

        self.datacollector = mesa.DataCollector(model_reporters={f"total_{resource}":
                                                                 lambda m,r=resource: sum(
                                                                     agent.inventory.get(r,0) for agent in m.agents
                                                                 )for resource in self.sd.resources
                                                                 },
                                                agent_reporters={"Usage":"base_usage"})

        usages = []
        inventories = []
        self.current_requests = []
        
        for _ in self.hosp_ids:
            usage,inventory = self.sd.generate_data()
            usages.append(usage)
            inventories.append(inventory)
        HostpitalAgent.create_agents(self,n,list(self.space.all_cells),usage=usages,inventory=inventories,init_state=self.state.normal)

        # for agent in self.agents:
        #     print("agent.unique_id:", agent.unique_id, 
        #   "cell node:", agent.cell.coordinate)
    
    def _max_donate(self,agent,resource):
        """In max, how much resource can a hospital donate"""
        cur_stock = agent.inventory.get(resource,0)
        min_stock = self.days_threshold*agent.base_usage.get(resource,0)
        return max(0,cur_stock-min_stock)

    def register_request(self,hospital: int,resource: str,amount: float,emergency: bool):
        """Put requests from agents in a queue"""

        self.requests.append({"hospital":hospital,"resource":resource,"amount":amount,"emergency":bool})
    
    def handle_requests(self):
        """Handle requests in the request queue that arrive at a particular time"""
        if len(self.requests) ==0:
            # print("INFO: No requests yet")
            return
        
        for request in list(self.requests):
            
            req_hosp = request.get("hospital","")
            req_resource = request.get("resource","")
            req_amt = request.get("amount",0)
            emergency = request.get("emergency",False)
            print(f"INFO: handling request from: {req_hosp}, resource: {req_resource}")

            self.requests.remove(request)

            if req_hosp=="" or req_resource=="":
                print("hosp or resource is empty/not there")
                continue

            if req_amt==0:
                return
            
            amt_left = req_amt
            req_agent = None
            for agent in self.agents:
                if agent.unique_id==req_hosp:
                    req_agent = agent
                    break
            for agent in self.agents:

                if amt_left<=0:
                    break
                if agent.unique_id == req_hosp:
                    continue
                if agent.days_remaining[req_resource] > self.days_threshold:
                    donatable = self._max_donate(agent,req_resource)
                    
                    actual_donatable = int(np.ceil(min(donatable,req_amt)))
                    
                    min_delay = 0
                    hosp_dist = self.G[req_agent.cell.coordinate][agent.cell.coordinate]["distance"]
                    for dist in self.min_dist_delay.keys():
                        if hosp_dist <=dist:
                            min_delay = self.min_dist_delay[dist]

                    actual_delay = random.randint(0,self.days_threshold) + min_delay
                    if agent.days_remaining[req_resource] < actual_delay:
                        continue
                    
                    transfer = {
                        'id': uuid.uuid4(),
                        'req_hospital':req_hosp,
                        'res_hospital':agent.unique_id,
                        'resource': req_resource,
                        'amount': actual_donatable,
                        'delay': actual_delay,
                        'distance':hosp_dist,
                        'emergency':emergency
                    }
                    self.pending_transfers.append(transfer)
                    
                    print(f"INFO: donor:{agent.unique_id}, amount: {actual_donatable}, delay: {actual_delay}")

    # def apply_transfers(self,user_feedback:dict):
    #     for transfer in self.pending_transfers:
    #         if user_feedback.get('id') == transfer.get('id'):
    #             for agent in self.agents:
    #                 if agent.unique_id == transfer.get('res_hospital'):
    #                     agent.inventory[transfer.get('resource')] -= transfer.get('acutal_donatable')
    #                     self.current_requests.append(transfer)
    #                     break
                    
      
    def restock_supplies(self):
        """Restock supplies after an interval or requested supplies arrive"""

        for cur_req in list(self.current_requests):
            if cur_req.get('delay') <=0:
                req_id = cur_req.get('req_hospital')
                resource = cur_req.get('resource')
                amt = cur_req.get('amount')
                for agent in self.agents:
                    if agent.unique_id == req_id:
                        agent.inventory[resource]+=amt

                self.current_requests.remove(cur_req)
            else:
                cur_req['delay']-=1

        if self.restock_interval<=0:
            for agent in self.agents:
                
                for resource in agent.inventory.keys():
                    restock = agent.base_usage.get(resource,0)*14
                    agent.inventory[resource] += restock
            self.restock_interval = 14
        else:
            self.restock_interval-=1
    
    def step(self):
        """A step in time"""
        self.datacollector.collect(self)
        self.handle_requests()
        self.restock_supplies()
        self.agents.shuffle_do("step")

