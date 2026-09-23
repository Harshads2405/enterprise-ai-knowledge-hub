# Advanced RAG — Deferred Work

This document tracks Advanced RAG capabilities that are intentionally deferred from the current implementation roadmap.

These items are not abandoned. They will be revisited later when they naturally fit into the Evaluation, Security, or Production phases, or when measured results show that they provide meaningful value.

---

## 1. True LLM-Based Multi-Query Retrieval

**Status:** Deferred

### Current State

The project already has multi-query retrieval and query decomposition.

Retrieval experiments were performed using the current deterministic multi-query approach.

The measured experiments did not demonstrate an improvement in the current evaluation dataset and introduced additional retrieval latency.

### Deferred Work

Implement and evaluate a true LLM-based multi-query retrieval strategy.

Expected flow:

```text
User Query
    ↓
LLM Query Generator
    ↓
Multiple Search Queries
    ↓
Hybrid Retrieval
    ↓
Candidate Merging
    ↓
Reranking
    ↓
Deduplication
    ↓
Top-K Results
###
This gives you a **single source of truth** for the remaining work instead of creating separate files for every deferred feature.