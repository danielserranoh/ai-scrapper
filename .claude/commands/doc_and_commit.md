---
name: doc_and_commit
description: Update documentation and create automated commit in one workflow
model: claude-sonnet-4-5-20250929
---

## Execution:

**Phase 1:** Execute `/update_docs` command with full session context

**Phase 2:** Invoke `@committer` agent with 1-2 sentence session summary

## Error Handling:
- If update_docs fails → stop, don't commit
- If committer fails → docs staged, user can manually commit or retry
- If Ollama not running → committer will notify and use fallback