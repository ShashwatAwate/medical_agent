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

def post_process_lineplot(chart):
    chart = chart.properties(
        width=400,
        height=400,
    ).configure_legend(
        strokeColor="black",
        fillColor="#ECE9E9",
        orient="right",
        cornerRadius=5,
        padding=10,
        strokeWidth=1,
    )
    return chart

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
    components = [],
    name = "Hosp Resource Network"
)

page
