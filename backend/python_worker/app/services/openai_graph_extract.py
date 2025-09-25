from __future__ import annotations
import json
from fastapi import HTTPException
from ..core.settings import settings

MERMAID_PROMPT = """
Your entire output must be ONLY a valid Mermaid graph definition.
It must start with "graph LR". Do not include the word "mermaid" at the beginning or any markdown fences (```).

Given an input PDF file, identify up to 10 most significant scientific concepts in the text and create a knowledge graph, highlighting scientific semantic (causal and otherwise) relationships among these concepts.

When extracting the relationships, focus on observations, definitions, lemmas, theorems,  experimental results, and conclusion.

Make sure that each concept is linked to at least one other concept in the knowledge graph with a relationship.

Make sure that there are at least 30 scientific relationship edges in the graph.

Separately indicate relationships that correspond to positive facts and negative facts, such as those that start with "does not" . For semantic relationships, limit yourself to those relationships that you can extract from the text, don't add your own knowledge to the graph not explicitly stated in the paper.

When generating negative relationships, do not use a conservative pipeline and do not only focus on sentences that explicitly contain cue words like “does not X,” “fails to X,” “unable to X,” etc.  If the manuscript describes the negative relationship indirectly, include the corresponding edge in the result.  In particular, for any positive relationship identified in the manuscript, see if you can identify any pair of nodes with a negative of that relationship: for every pair of entities that appears anywhere in the manuscript, you must output a negative edge whenever the text states—explicitly or implicitly—that the relationship does not hold for that pair. If the manuscript rules out a relationship explicitly or implicitly, include the negative edge.

Before producing the final graph, run a consistency check: if an entity A has a relationshipwith entity B — i.e., R(A,B) is true, scan for explicit or implicit sentences testing for the relationship \neg R(A, *) and   \neg R(*, B).

Generate all negative edges before filtering/limiting the output size; do not omit them in favor of additional positive edges.

Since negative relationships can be important, please include prioritize them in the output.

Use this exact syntax for nodes: Concept_ID["Concept Label (★★★)"]. The Concept_ID should be the concept name with spaces replaced by underscores.

Annotate the nodes with their strength in the document. Node strength ≈ relative prominence in the manuscript (★☆☆ = mentioned a few times, ★★☆ = recurrent, ★★★ = core idea).

Annotate the edges in the knowledge graph with the relationships type. Also annotate each edge regarding how certain you are with the relationship based on your analysis of the text  (★☆☆ = not certain at all, ★★☆ = almost certain, ★★★ = very certain).

Use this exact syntax for positive relationships: Node_A -- "relationship (★★★)" --> Node_B.

For negative relationships, use dotted lines and label the edge as "does_not_X". Use this exact syntax: Node_A -. "does_not_relationship (★★★)" .-> Node_B.

In the output, list first al the positive edges, followed with the negative edges.

Please be verbose in the graph. Please do not output anything else; outputting just the graph is sufficient.
"""

def _fake_extract_graph(text: str, filename: str) -> str:
    # Deterministic placeholder for no-key environments
    return f"""
graph LR
    Vemurafenib["Vemurafenib (★★★)"]
    BRAF_V600E["BRAF V600E (★★☆)"]
    MEK_inhibitors["MEK inhibitors (★★☆)"]
    Response_Rates["Response Rates (★☆☆)"]
    Resistance["Resistance (★☆☆)"]

    Vemurafenib -- "targets (★★★)" --> BRAF_V600E
    MEK_inhibitors -- "improves (★★☆)" --> Response_Rates
    MEK_inhibitors -- "reduces (★★☆)" --> Resistance
    Vemurafenib -. "does_not_inhibit (★★★)" .-> MEK_inhibitors
"""

def extract_graph(text: str, filename: str) -> str:
    if settings.openai_dry_run or not settings.openai_api_key:
        return _fake_extract_graph(text, filename)

    try:
        # Lazy import to avoid hard dependency if not used
        import os
        import httpx
        from openai import OpenAI

        # Honor proxy environment variables without using unsupported kwargs
        proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("OPENAI_PROXY")
        http_client = None
        if proxy_url:
            http_client = httpx.Client(proxies=proxy_url, timeout=60.0)

        client = OpenAI(api_key=settings.openai_api_key, http_client=http_client) if http_client else OpenAI(api_key=settings.openai_api_key)
        
        # We add the filename to the user content for the LLM to use in citations
        user_content = f"FILENAME: {filename}\n\nTEXT:\n{text}"
        
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": MERMAID_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content
        return content
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI graph extraction failed: {exc}")
