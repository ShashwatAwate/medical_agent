import math
import solara
from mesa.visualization import (
    Slider,
    SolaraViz,
    SpaceRenderer,
    make_plot_component,
)
from mesa.visualization.components import AgentPortrayalStyle
from .agents import State
from .models import HospitalModel
from .data.generate_data import SyntheticData

sd = SyntheticData()

def agent_potrayal(agent):
    node_color = {
        State.normal : "blue",
        State.emergency : "red",
        State.request : "green"
    }
    return AgentPortrayalStyle(color=node_color[agent.state],size=20)

model_params = {
    "n": Slider(
        label="Number of agents",
        value=5,
        min=5,
        max=15,
        step=1
    )
}

InventoryPlot = make_plot_component(
    {
        f"total_{resource}":None
        for resource in sd.resources
    }
)

model1 = HospitalModel()
renderer = SpaceRenderer(HospitalModel(n=5))

renderer.draw_structure(
    node_kwargs={
        "node_color": "lightgray",
        "node_size": 800,
        "edgecolors": "black",
        "linewidths": 2,
    },
    edge_kwargs={
        "style": "dashed",
    },
)

renderer.draw_agents(agent_potrayal)

renderer.render()

page = SolaraViz(
    model1,
    renderer,
    model_params=model_params,
    components = [InventoryPlot],
    name = "Hosp Resource Network"
)

page
