from langgraph.graph import StateGraph,START,END

from .core import State

from data_ingestor import ingest_data

graph_builder = StateGraph(State)

#NODES

graph_builder.add_node(ingest_data)


#EDGES
graph_builder.add_edge(START,"ingest_data")