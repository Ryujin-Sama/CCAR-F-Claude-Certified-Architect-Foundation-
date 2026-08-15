# =============================================================================
# TOOL MISROUTING EXAMPLE - Demonstrates improper vs. proper tool usage
# =============================================================================
# This module showcases the distinction between:
# 1. Vague/minimal tool descriptions that lead to misuse
# 2. Clear, detailed tool specifications that prevent tool misrouting
#
# Tool misrouting occurs when an agent incorrectly selects a tool due to
# ambiguous descriptions, leading to poor performance and wasted API calls.
# =============================================================================

# INITIAL DEFINITION: Minimal/Vague Tool Descriptions (POOR PRACTICE)
# =====================================================================
# These descriptions are too brief and lack important usage context.
# This can cause agents to:
#   - Confuse search_web with search_documents
#   - Use analyze_content as a search tool instead of an analysis tool
#   - Make unnecessary API calls to wrong tools
# =====================================================================
tools = [
    {
        # Basic web search tool with minimal description
        "name": "search_web",
        "description":"Search for Information"
    },
    {
        # Document search tool with ambiguous naming
        "name":"search_documents",
        "description":"Search documents for information"
    },
    {
        # Content analysis tool with unclear purpose
        "name":"analyze_content",
        "description": "Analyze and extract information from content"
    }
]

# IMPROVED DEFINITION: Comprehensive Tool Descriptions (BEST PRACTICE)
# ===================================================================
# These detailed descriptions clarify each tool's purpose, when to use it,
# what inputs/outputs it provides, and crucially WHEN NOT to use it.
# This prevents tool misrouting by being explicit about tool boundaries.
# ===================================================================
tools =[
    {
        # Web search tool - for real-time, external information retrieval
        "name" : "search_web",
        "description":"""
                    Query live web pages via search engine. Use for current events,
                    recent publications, URLs not yet in the document corpus.
                    Input: query string, Returns ranked URLs + snippets.
                    Do NOT use for documents already loaded into the research corpus.
                    """
    },
    {
        # Document corpus search tool - for pre-indexed, known documents
        "name":"search_documents",
        "description":"""
                    Full-text search across the pre-loaded research corpus (PDFs, reports, cached articles).
                    Use ONLY for documents already ingested. Faster and more precise then web search for known soruces.
                    INPUT: query string + optional doc_id filter.
                    Do NOT use to find new sources -use search_web for that.
        """
    },
    {
        # Content analysis tool - for deep examination of retrieved content
        "name":"analyze_content",
        "description":"""
                    Deep analysis of a specific piece of content already retrieved.
                    Extracts key claims, identifies contradictions, accesses credibility.
                    Input: content (string), analysis_type (claims|contradictions|summary).
                    Use AFTER search_web or search_documents - not as a search tool itself.
"""
    }
]