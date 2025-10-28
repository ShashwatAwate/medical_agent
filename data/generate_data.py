import pandas as pd
import numpy as np
from datetime import timedelta,datetime
import random

import os

class SyntheticData:

    def __init__(self,save_path: str):
        self.save_path = save_path
        self.reports = pd.DataFrame()
        self.simulation = pd.DataFrame()

    def generate_reports(self,region_name: str,resource_name:str,date: datetime):
        """Generates some reports justifying a resource spike in a region or for a hospital"""

        disaster_events = ["flood","epidemic","earthquake","explosion"]
        weather_events = ["heat wave","blizzard","heavy rain","storm"]
        seasonal_events = ["flu outbreak", "pollen allergy surge", "tourist season", "festival crowd"]
        

        category = random.choice(["disaster","weather","seasonal"])

        if category == "disaster":
            event = random.choice(disaster_events)
            reason = f"A {event} in {region_name} has led to increased influx of patients to hospitals"
        elif category=="weather":
            event = random.choice(weather_events)
            reason = f"Ongoing {event} in {region_name} has strained supplies across hospitals"
        elif category == "seasonal":
            event = random.choice(seasonal_events)
            reason = f"During {event}, a rise in {resource_name} usage was reported."

        try:
            new_report = pd.DataFrame(
                {"report":reason},
                index = [pd.to_datetime(date)]
            )
            new_report.index.name = "date"
            self.reports = pd.concat((self.reports,new_report))

        except Exception as e:
            print(f"ERROR:{str(e)}\n LOC: appending to dataframe after generating report: {reason}")
            return 



    def generate_data(self,n_hospitals = 5, n_days = 130,resources = ["oxygen","ventilators","medication_TB","ppe_kits"],start_date = "2025-01-01",seed = 42,window = 7) :
        """Generates a simulation of n_days with random usage spikes and uses given resources"""
        np.random.seed(seed)
        random.seed(seed)

        hospitals = [f"hos_{i+1}" for i in range(n_hospitals)]
        regions = ["north","south","east","west","central"]

        start = datetime.strptime(start_date,"%Y-%m-%d")
        data = []

        for hospital in hospitals:
            region = random.choice(regions)
            for resource in resources:
                #randomly determine current stock for a resource and its base daily usage
                current_stock = random.randint(200,800)
                base_usage = random.randint(10,40)
                resource_threshold = random.randint(10,40)
                
                usage_history = []

                next_restock = -1
                for day in range(n_days):
                    if(day==next_restock):
                        current_stock += random.randint(200,800)
                        next_restock = -1

                    date = start + timedelta(days=day)

                    usage = np.random.normal(base_usage,5)
                    if random.random()<0.05:
                        usage *= random.randint(2,4)

                    usage_history.append(usage)

                    if len(usage_history)>window:
                        usage_history.pop(0)

                    if len(usage_history)== window:
                        rolling_avg = np.mean(usage_history)

                        if usage> rolling_avg*1.8:
                            self.generate_reports(region_name=region,resource_name=resource,date=date)

                    lead_time = random.randint(1,3)
                    supplier_delay = random.randint(0,4)


                    current_stock -= usage 

                    if current_stock <= resource_threshold:
                        next_restock = day + lead_time+ supplier_delay

                    if(current_stock<0):
                        current_stock=0

                    data.append({
                        "hospital":hospital,
                        "region":region,
                        "resource":resource,
                        "date":date,
                        "usage":usage,
                        "current_stock":current_stock,
                        "lead_time":lead_time,
                        "supplier_delay":supplier_delay
                    })

        df = pd.DataFrame(data)
        self.simulation = df

    def write_dataframes(self):
        """write simulation data to persistent storage"""
        try:
            sim_path =  os.path.join(self.save_path,"simulation.csv")
            report_path = os.path.join(self.save_path,"reports.csv")

            self.simulation.to_csv(sim_path)
            self.reports.to_csv(report_path)
            
        except Exception as e:
            print(f"ERROR:{str(e)} during writing dataframes to disk ")
            return
        



if __name__ == "__main__":
    pass
    sd = SyntheticData("./sim_data")
    sd.generate_data()
    sd.write_dataframes()

                    
                