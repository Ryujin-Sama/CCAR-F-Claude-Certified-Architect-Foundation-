import anthropic

# Create one Anthropic client that will be reused for every session operation in
# this script. The SDK obtains authentication and other connection settings from
# the environment, so the script does not need to put credentials in source code.
client = anthropic.Anthropic();

# This identifies the existing analysis session that serves as the common starting
# point. Each fork below inherits the baseline conversation while receiving a
# different instruction, allowing the alternatives to be evaluated independently.
baseline_session_id = "baseline-arch-analysis-001"

# Fork the baseline to investigate a service-layer refactoring. This branch is
# deliberately kept separate from the other proposal so its conclusions are not
# mixed with the CQRS investigation.
fork_a = client.beta.sessions.fork(
    session_id=baseline_session_id,
    system_prompt_addition="Explore refactoring approach A: extract service layer pattern."
)

# Create a second independent branch of the same baseline session. This branch
# explores CQRS, which gives the analysis a contrasting architectural direction
# without modifying the original baseline session or branch A.
fork_b = client.beta.sessions.fork(
    session_id=baseline_session_id,
    system_prompt_addition="Explore refactoring approach B: CQRS pattern."
)

# Keep earlier findings as context for the next analysis rather than treating them
# as authoritative facts. The architecture may have changed since the summary was
# written, so the fresh analysis must confirm each claim against the current code.
prior_finding_summary = """
PRIOR ANALYSIS SUMMARY (from 2026-06-10):
-Architecture: monolith, Django 4.2, PostgreSQL 15, Redis 5.0.1
-Key coupling points: auth and billing share the user model directly
-Identified debt: payment_service.py has 3 untested code paths
-Recommended next steps: extract billing into separate bounded context

NOTE: This summary is from 2 days ago, The codebase has since been updated.
Please treat these as hypotheses and validate, not established facts.
Re-explore the current file structure before acting on the findings.
"""

# Build the initial user message for a new analysis request. The previous summary
# is included to preserve useful historical context, while the final instruction
# explicitly requires the agent to re-check the current file structure first.
message = [
    {
        "role": "user",
        "content": prior_finding_summary + "\n\nNow please begin fresh analysis of the current codebase state."
    }
]