"""Step 5: prompt construction.

Uses chat messages (system + user); Ollama applies the model's own chat
template, so no hand-written special tokens.
"""

SYSTEM_WITH_SCHEMA = """You are a Text-to-SQL assistant for a Brazilian e-commerce SQLite database.
Write ONE SQLite SELECT query that answers the user's question, using only the tables and columns in <schema>.

Rules:
- Use SQLite syntax. For dates use strftime (e.g. strftime('%Y', col)); SQLite has no YEAR() or DATE_TRUNC().
- Use only tables and columns that appear in <schema>. Do not invent names.
- If <examples> are given, follow their join paths and conventions.
- Return only the SQL query: no explanation and no markdown.
- If the question needs data that is not available in <schema>, return exactly: -- UNAUTHORIZED"""

SYSTEM_NO_SCHEMA = """You are a Text-to-SQL assistant for a Brazilian e-commerce SQLite database.
Write ONE SQLite SELECT query that answers the user's question.
Use SQLite syntax. Return only the SQL query: no explanation and no markdown."""


def build_messages(question: str, schema_text: str | None = None, examples: list | None = None) -> list:
    parts = []
    if schema_text:
        parts.append(f"<schema>\n{schema_text}\n</schema>")
    if examples:
        shots = "\n\n".join(f"Question: {e['question']}\nSQL: {e['sql']}" for e in examples)
        parts.append(f"<examples>\n{shots}\n</examples>")
    parts.append(f"<question>\n{question}\n</question>")
    system = SYSTEM_WITH_SCHEMA if schema_text else SYSTEM_NO_SCHEMA
    return [{"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(parts)}]


def render_prompt(messages: list) -> str:
    """Human-readable view of the final prompt (for the Milestone 1 demo)."""
    return "\n\n".join(f"<|{m['role']}|>\n{m['content']}" for m in messages) + "\n\n<|output|>"
