from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.core.config import Settings
from app.workflow.nodes import (
    CapabilityJudgeNode,
    EvidenceSelectorNode,
    ImpactAnalyzerNode,
    InputNormalizerNode,
    KnowledgeRetrieverNode,
    MissingInfoAnalyzerNode,
    PersistenceNode,
    ReportComposerNode,
    RequirementParserNode,
    RetrievalPlannerNode,
    RiskAnalyzerNode,
)
from app.workflow.state import PreReviewState


class PreReviewWorkflow:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(PreReviewState)

        graph.add_node("input_normalizer", InputNormalizerNode(self.settings))
        graph.add_node("requirement_parser", RequirementParserNode())
        graph.add_node("retrieval_planner", RetrievalPlannerNode())
        graph.add_node("knowledge_retriever", KnowledgeRetrieverNode())
        graph.add_node("evidence_selector", EvidenceSelectorNode())
        graph.add_node("capability_judge", CapabilityJudgeNode())
        graph.add_node("missing_info_analyzer", MissingInfoAnalyzerNode())
        graph.add_node("risk_analyzer", RiskAnalyzerNode())
        graph.add_node("impact_analyzer", ImpactAnalyzerNode())
        graph.add_node("report_composer", ReportComposerNode())
        graph.add_node("persistence_node", PersistenceNode())

        graph.set_entry_point("input_normalizer")
        graph.add_edge("input_normalizer", "requirement_parser")
        graph.add_edge("requirement_parser", "retrieval_planner")
        graph.add_edge("retrieval_planner", "knowledge_retriever")
        graph.add_edge("knowledge_retriever", "evidence_selector")
        graph.add_edge("evidence_selector", "capability_judge")
        graph.add_edge("capability_judge", "missing_info_analyzer")
        graph.add_edge("missing_info_analyzer", "risk_analyzer")
        graph.add_edge("risk_analyzer", "impact_analyzer")
        graph.add_edge("impact_analyzer", "report_composer")
        graph.add_edge("report_composer", "persistence_node")
        graph.add_edge("persistence_node", END)

        return graph.compile()

    def invoke(self, initial_state: PreReviewState) -> PreReviewState:
        return self._graph.invoke(initial_state)

