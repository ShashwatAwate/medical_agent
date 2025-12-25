import pandas as pd
import numpy as np
from datetime import timedelta,datetime
import random

import os

class SyntheticData:

    def __init__(self,resources = ["oxygen","ventilators","medication_TB","ppe_kits"]):
        self.resources = resources
        self.regions = ["north","south","east","west","central"]

    def generate_data(self,seed = 42) :
        """Generates a simulation of n_weeks with random usage spikes and uses given resources"""

        np.random.seed(seed)
        random.seed(seed)

        resource_data = {}
        for resource in self.resources:
            #randomly determine current stock for a resource and its base usage
            current_stock = random.randint(200,800)
            base_usage = current_stock*random.uniform(0.03,0.08)
            resource_data[resource] = {"usage":base_usage,"stock" : current_stock}
        usage = {}
        inventory = {}
        for resource in resource_data.keys():
            inventory[resource] = resource_data[resource]["stock"]
            usage[resource] = resource_data[resource]["usage"]
        
        return usage,inventory


    def generate_reports(self):
        """Make unstructured reports stating for justifying some random spikes in daily queries"""

        disaster_events = [
            ("flood", "flooding"),
            ("earthquake", "seismic activity"),
            ("explosion", "industrial accident"),
            ("epidemic", "infectious disease outbreak")
        ]
        weather_events = [
            ("heat wave", "rising temperatures"),
            ("blizzard", "extreme cold"),
            ("heavy rain", "monsoon rains"),
            ("storm", "high wind and rainfall")
        ]
        seasonal_events = [
            ("flu outbreak", "seasonal flu cases"),
            ("pollen allergy surge", "spring allergies"),
            ("tourist season", "tourist inflow"),
            ("festival crowd", "festival gatherings")
        ]


        hospital_name = f"hosp_{random.randint(1,self.n_hospitals)}"
        region_name = random.choice(self.regions)
        resource_name = random.choices(self.resources)


        severities = ["mild", "moderate", "severe", "critical"]
    
        category = random.choices(
            ["disaster", "weather", "seasonal", "no_spike"],
            weights=[0.2, 0.3, 0.3, 0.2]
        )[0]

        if category == "disaster":
            event, descriptor = random.choice(disaster_events)
            severity = random.choice(severities)
            reason = random.choice([
                f"A {severity} {event} in {region_name} has overwhelmed hospitals with new patients needing {resource_name}.",
                f"Due to {descriptor} in {region_name}, {hospital_name} is reporting higher {resource_name} consumption.",
                f"Emergency teams responding to the {event} are utilizing significant {resource_name} stock."
            ])
        elif category == "weather":
            event, descriptor = random.choice(weather_events)
            severity = random.choice(severities)
            reason = random.choice([
                f"The ongoing {event} has caused a {severity} strain on {resource_name} across {region_name}.",
                f"Weather reports indicate {descriptor} leading to increased patient admissions and {resource_name} use.",
                f"In {region_name}, {hospital_name} is facing logistical issues for {resource_name} distribution due to {event}."
            ])
        elif category == "seasonal":
            event, descriptor = random.choice(seasonal_events)
            reason = random.choice([
                f"During {event}, hospitals in {region_name} saw a steady rise in {resource_name} demand.",
                f"{hospital_name} noted higher {resource_name} usage due to {descriptor}.",
                f"{event.capitalize()} has mildly increased the need for {resource_name}."
            ])
        else:
            reason = random.choice([
                f"No significant {resource_name} spikes reported at {hospital_name}.",
                f"{hospital_name} reports stable operations; no shortages detected.",
                f"Normal activity levels observed in {region_name} for {resource_name}."
            ])


        if "increased" in reason or "higher" in reason or "overwhelmed" in reason:
            delta = random.randint(10, 40)
            reason += f" Estimated {resource_name} usage has risen by about {delta}%."

        return reason


if __name__ == "__main__":
    pass
    sd = SyntheticData("./sim_data")
    sd.generate_data()
    
    # print(sd.generate_reports())

                    
                