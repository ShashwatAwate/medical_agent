from langgraph.graph import StateGraph,START,END


from .core import State

from data_ingestor import ingest_knowledge,ingest_daily_reports


graph_builder = StateGraph(State)

#NODES

graph_builder.add_node(ingest_knowledge)
graph_builder.add_node(ingest_daily_reports)

#EDGES
graph_builder.add_edge(START,"ingest_knowledge")
graph_builder.add_edge("ingest_knowledge","ingest_daily_reports")
