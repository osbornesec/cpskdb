# Task Completion Checklist

## When a Task is Completed

### Code Quality Checks

1. **Run Linters and Formatters**

   ```bash
   black src/ tests/
   ruff check --fix src/ tests/
   mypy src/
   ```

2. **Run All Tests**

   ```bash
   pytest tests/unit/
   pytest tests/integration/
   pytest tests/e2e/
   pytest --cov=src --cov-report=term-missing
   ```

3. **Pre-commit Hooks**

   ```bash
   pre-commit run --all-files
   ```

### Documentation Updates

- [ ] Update docstrings for new/modified functions
- [ ] Update API documentation if endpoints changed
- [ ] Add inline comments for complex logic
- [ ] Update README.md if setup/usage changed

### Code Review Checklist

- [ ] Code follows PEP 8 style guide
- [ ] All functions have type hints
- [ ] No hardcoded values (use config/constants)
- [ ] Error handling is comprehensive
- [ ] No sensitive data in logs or commits
- [ ] Performance considerations addressed
- [ ] Security best practices followed

### Testing Verification

- [ ] Unit tests cover new functionality
- [ ] Integration tests for component interactions
- [ ] Edge cases and error conditions tested
- [ ] Test coverage ≥80% for new code
- [ ] All existing tests still pass

### Before Marking Complete

1. **Verify functionality works as expected**
2. **Check for any TODO/FIXME comments**
3. **Ensure no debug code remains**
4. **Validate against acceptance criteria**
5. **Update task status in .ai/docs/tasks.md**

### Final Commands to Run

```bash
# Full quality check sequence
make lint      # Or manual: black + ruff + mypy
make test      # Or manual: pytest
make coverage  # Check test coverage
```

## Important Reminders

- ALWAYS use Serena MCP tools for code operations
- ALWAYS use @agent-context7-docs-searcher before implementing
- Follow TDD methodology: test first, implement second
- Keep commits atomic and well-described
- Never commit without running tests
