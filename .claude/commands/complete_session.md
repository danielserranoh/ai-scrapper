# Complete Development Session

This command performs a full session completion workflow by combining multiple tasks.

**Execute in sequence:**

1. **Update Implementation Tracking**:
   - Review current todo list and mark completed items as done
   - Update the "Current Todo List (Active Session)" section with remaining work
   - Update "Session Handoff Notes" with current pipeline status
   - Update the "Last Updated" timestamp in IMPLEMENTATION_TRACKER.md

2. **Update Documentation**:
   - Update README.md with latest information
   - Ensure code passes linting and type checking with `ruff check .`

3. **Commit Changes**:
   - Use `gh` to commit the changes with a descriptive commit message
   - Include progress achieved and any bug fixes
   - Push changes but do NOT create a PR unless explicitly requested

**Guidelines:**
- Be thorough with documentation updates
- Include specific file locations and implementation details
- Test the pipeline with `python main.py crawl cs.stanford.edu --max-pages 3 --verbose`
- Use descriptive commit messages that summarize the session's achievements

This replaces the need to chain `/update_tracking` + `/doc_and_commit` commands.