"""Tests for the agent discovery service."""

import pytest

from wowasi_ya.core.agent_discovery import AgentDiscoveryService
from wowasi_ya.models.project import ProjectInput


class TestAgentDiscoveryService:
    """Tests for AgentDiscoveryService."""

    def test_analyze_project_finds_healthcare_domain(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that healthcare keywords are detected."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)

        domain_names = [d.domain for d in domains]
        assert "healthcare" in domain_names

    def test_analyze_project_finds_tribal_domain(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that tribal governance keywords are detected."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)

        domain_names = [d.domain for d in domains]
        assert "tribal_governance" in domain_names

    def test_analyze_project_finds_rural_domain(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that rural community keywords are detected."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)

        domain_names = [d.domain for d in domains]
        assert "rural_community" in domain_names

    def test_analyze_project_no_domains_for_minimal(
        self, sample_project_minimal: ProjectInput
    ) -> None:
        """Test that minimal project has fewer domain matches."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project_minimal)

        # Simple task tracking app shouldn't match specific domains
        assert len(domains) <= 1

    def test_generate_agents_creates_agents(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that agents are generated from domain matches."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)
        agents = service.generate_agents(sample_project, domains)

        assert len(agents) > 0
        for agent in agents:
            assert agent.id.startswith("agent_")
            assert len(agent.research_questions) > 0
            assert len(agent.search_queries) > 0

    def test_discover_returns_both_domains_and_agents(
        self, sample_project: ProjectInput
    ) -> None:
        """Test the full discovery pipeline."""
        service = AgentDiscoveryService()
        domains, agents = service.discover(sample_project)

        assert len(domains) > 0
        assert len(agents) > 0
        # Should have roughly 2 agents per domain
        assert len(agents) >= len(domains)

    def test_confidence_scores_are_valid(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that confidence scores are in valid range."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)

        for domain in domains:
            assert 0.0 <= domain.confidence <= 1.0

    def test_domains_sorted_by_confidence(
        self, sample_project: ProjectInput
    ) -> None:
        """Test that domains are sorted by confidence descending."""
        service = AgentDiscoveryService()
        domains = service.analyze_project(sample_project)

        if len(domains) > 1:
            for i in range(len(domains) - 1):
                assert domains[i].confidence >= domains[i + 1].confidence
