"""
subagent_context.py
Example context and payload templates used when coordinating research subagents.

Purpose:
- Provide sample `research_findings` that a web/search subagent might return.
- Show a `synthesis_prompt` that a synthesis subagent could consume.
- Include example `task_call`, `intermediate_output`, and `conflict` objects
  to illustrate intermediate data shapes produced during orchestration.
- Include `resume_context` text to demonstrate how a coordinator can ask
  subagents to resume work after a previous session.

Notes:
- This file is intended as documentation/examples rather than production
  runtime code. Adjust fields and schemas to match your orchestration
  framework and serialization conventions.
"""

# Standard library import needed by `synthesis_prompt` below which
# serializes the `research_findings` list into the prompt text.
import json


# --- Example research findings ---
# `research_findings` is a sample list representing results returned
# from a web/search subagent. Each entry contains the discovery text,
# a source URL and metadata useful for provenance and citation.
# Real subagents would produce similar dicts; keep the shape stable
# so downstream synthesis and citation tools can consume them.
research_findings = [
    {
        "finding": "Claude' tool_use stop_reason requires the full assistant message to be appended before tool results.",
        "source_url": "https://docs.anthropic.com/agents/tool-use",
        "source_title": "Anthropic Tool Use Documentation",
        "page_number": None,
        "retrieved_at": "2024-06-10T12:00:00Z",
        "confidence": "high"
    },
    {
        "finding": "Using an interation cap as a primary stop condition is an anti-pattern.",
        "source_url": "https://docs.anthropic.com/agents/loops",
        "source_title": "Anthropic Loops Best Practices",
        "page_number": None,
        "retrieved_at": "2024-06-10T12:05:00Z",
        "confidence": "high"
    }
]


# `synthesis_prompt` is the natural-language prompt that would be sent
# to a synthesis subagent. It embeds the `research_findings` (JSON
# serialized) so the worker can produce a structured report with
# citations and conflict detection.
synthesis_prompt = f"""
You are a research synthesis agent. Your task is to produce a structured research report.

FINDINGS TO SYNTHESIZE:
{json.dumps(research_findings, indent=2)}

Requirements:
-Every claim in the report MUST cite its source_url
-Preserve the retrieved_at date for temporal accuracy
-Flag any conflicting findings with both sources annotated
-Output format: JSON with keys: 'summary', 'findings', 'conflicts', 'sources'
"""


# `task_call` demonstrates how a coordinator might package a `tool_use`
# invocation for a `Task` subagent. The `input.prompt` includes the
# `synthesis_prompt` (which already embeds `research_findings`). Use
# this as a template for sending synthesis jobs to worker agents.
task_call = {
    "type": "tool_use",
    "name": "Task",
    "input": {
        "description": "Synthesis Research findings into a structured report",
        "prompt": synthesis_prompt,
    }
}


# `intermediate_output` is an example of structured data a synthesis
# subagent might return before final reporting. It separates claims,
# sources (with stable `source_id` references), and any detected
# conflicts to enable automated conflict-resolution steps.
intermediate_output = {
    "claims": [
        {
            "claim_id": "c001",
            "text": "Subagents do not inherit coordinator conversation history.",
            "source_id": "src_001",
            "confidence": "high"
        },
        {
            "claim_id": "c002",
            "text": "Parallel subagents require multiple Task calls in one coordinator response.",
            "source_id": "src_002",
            "confidence": "high"
        }
    ],
    "sources": [
        {
            "source_id": "src_001",
            "source_url": "https://docs.anthropic.com/agents/multi-agent",
            "source_title": "Anthropic Multi-Agent Architecture Guide",
            "retrieved_at": "2024-06-10T12:10:00Z"
        },
        {
            "source_id": "src_002",
            "source_url": "https://docs.anthropic.com/agents/task-tool",
            "source_title": "Anthropic Task Tool Reference",
            "retrieved_at": "2024-06-10T12:15:00Z"
        }
    ],
    "conflicts": []
}


# `conflict` shows the shape used to represent two opposing claims
# on the same topic. A coordinator can collect these and attempt
# to resolve them, or surface them to a human reviewer.
conflict = {
    "conflict_id": "conf_001",
    "topic": "Parallel subagent invocation",
    "claim_a": {
        "text": "Multiple Task calls in one repsonse run in parallel.",
        "source_id": "src_002"
    },
    "claim_b": {
        "text": "Task calls are always sequential regardless of placement.",
        "source_id": "src_003"
    },
    "resolution": "unresolved"
}


# `resume_context` is plain text the coordinator might include when
# asking subagents to pick up work after an interruption; it lists
# changed files and any outstanding todos so the subagent can focus
# re-analysis on deltas rather than re-processing everything.
resume_context = """
Resuming from previous analysis session.

CHANGES SINCE LAST SESSION:
-auth/middleware.py has been modified (new rate limiting added)
-requirements.txt updated(added redis==5.0.1)
-The TODO in payemnt_service.py line 142 has NOT been addressed yet

Please re-analyse only the changed files and continue from your prior findings.
"""