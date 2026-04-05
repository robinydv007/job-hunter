"""LangGraph workflow definition for the job hunter pipeline."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from job_hunter.graph.nodes import (
    export_csv_node,
    filter_shortlist_node,
    load_config_node,
    parse_resume_node,
    score_jobs_node,
    search_jobs_node,
)
from job_hunter.graph.state import JobHunterState


def build_workflow():
    """Build the LangGraph workflow for the job hunter pipeline."""
    workflow = StateGraph(JobHunterState)

    # Add nodes
    workflow.add_node("load_config", load_config_node)
    workflow.add_node("parse_resume", parse_resume_node)
    workflow.add_node("search_jobs", search_jobs_node)
    workflow.add_node("score_jobs", score_jobs_node)
    workflow.add_node("filter_shortlist", filter_shortlist_node)
    workflow.add_node("export_csv", export_csv_node)

    # Define edges (linear pipeline)
    workflow.add_edge("load_config", "parse_resume")
    workflow.add_edge("parse_resume", "search_jobs")
    workflow.add_edge("search_jobs", "score_jobs")
    workflow.add_edge("score_jobs", "filter_shortlist")
    workflow.add_edge("filter_shortlist", "export_csv")
    workflow.add_edge("export_csv", END)

    workflow.set_entry_point("load_config")

    return workflow.compile()
