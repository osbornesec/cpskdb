# CRITICAL: CODE OPERATIONS RULE
  For ALL code search and editing operations:
  1. Use Serena MCP tools (find_symbol, replace_symbol_body, etc.) as PRIMARY method
  2. Use @agent-context7-docs-searcher for all documentation research
  3. Traditional tools (grep, sed) are FALLBACK ONLY
  4. This applies to ALL agents and subagents

## IMPORTANT: Documentation Research Before Coding
  **ALWAYS use @agent-context7-docs-searcher BEFORE writing any code:**
  - Invoke this subagent to research language, library, and framework usage
  - Provides best practices, patterns, and implementation guidance
  - Ensures code follows current standards and avoids antipatterns
  - Example: `@agent-context7-docs-searcher "Research React hooks best practices for data fetching"`

## Serena MCP Server - Semantic Code Intelligence

### Overview
Serena MCP is a semantic code analysis and manipulation server that provides intelligent, symbol-aware operations for codebases. It should be used as the PRIMARY method for ALL code operations, with traditional tools (grep, sed, etc.) only as fallbacks.

### Core Capabilities

#### Search Code (ALWAYS use these first)
- **Find symbols**: `mcp__serena__find_symbol(name_path="ClassName", include_body=true)`
  - Searches for code entities by name path pattern
  - Supports depth parameter to retrieve children (e.g., methods of a class)
  - Can include/exclude specific symbol kinds (classes, functions, variables, etc.)
  
- **Find references**: `mcp__serena__find_referencing_symbols(name_path="methodName", relative_path="file.py")`
  - Finds all references to a specific symbol
  - Returns metadata and code snippets around references
  
- **Pattern search**: `mcp__serena__search_for_pattern(substring_pattern="TODO|FIXME")`
  - Flexible regex search across codebase
  - Supports file inclusion/exclusion globs
  - Can restrict to code files only
  
- **Symbol overview**: `mcp__serena__get_symbols_overview(relative_path="src/")`
  - High-level understanding of symbols in a file
  - Shows top-level classes, functions, variables
  - Essential first step when exploring new files

#### File Operations
- **List directory**: `mcp__serena__list_dir(relative_path=".", recursive=true)`
  - Lists non-gitignored files and directories
  
- **Find files**: `mcp__serena__find_file(file_mask="*.py", relative_path=".")`
  - Finds files matching patterns using wildcards

#### Edit Code (PREFER symbol-based operations)
- **Replace symbol body**: `mcp__serena__replace_symbol_body(name_path="functionName", relative_path="file.py", body="new code")`
  - Replaces entire function/class/method body
  - Preserves indentation and context
  
- **Insert before symbol**: `mcp__serena__insert_before_symbol(name_path="className", body="imports")`
  - Ideal for adding imports or new top-level definitions
  
- **Insert after symbol**: `mcp__serena__insert_after_symbol(name_path="methodName", body="new method")`
  - Adds new methods, functions, or classes after existing ones

#### Memory Management
- **Write memory**: `mcp__serena__write_memory(memory_name="architecture_overview", content="...")`
  - Store important project information for future reference
  
- **Read memory**: `mcp__serena__read_memory(memory_file_name="architecture_overview.md")`
  - Retrieve stored project knowledge
  
- **List memories**: `mcp__serena__list_memories()`
  - View all available memory files

#### Project Management
- **Check onboarding**: `mcp__serena__check_onboarding_performed()`
  - Verify if project onboarding is complete
  
- **Onboarding**: `mcp__serena__onboarding()`
  - Initialize project understanding

#### Thinking Tools (Use strategically)
- **Think about collected information**: `mcp__serena__think_about_collected_information()`
  - Call after completing search sequences
  
- **Think about task adherence**: `mcp__serena__think_about_task_adherence()`
  - Call before making code changes
  
- **Think about whether done**: `mcp__serena__think_about_whether_you_are_done()`
  - Call when task appears complete

### Best Practices

1. **Symbol-based editing over text replacement**
   - Use symbol operations for entire functions/classes
   - Only use regex for small, targeted changes within symbols

2. **Efficient code exploration**
   - Start with `get_symbols_overview` for new files
   - Use `find_symbol` with `include_body=false` first
   - Only read full bodies when necessary

3. **Name path patterns**
   - Simple name: `"method"` - matches any method
   - Relative path: `"class/method"` - method within class
   - Absolute path: `"/class/method"` - top-level class method

4. **Always verify before editing**
   - Use thinking tools before code changes
   - Find references before modifying public APIs
   - Check for test files that may need updates

## Knowledge Management Integration

### Documentation Research

**Use @agent-context7-docs-searcher for all documentation needs:**
- Technical guidance and best practices
- Library and framework usage
- Implementation patterns
- API documentation

**Usage Guidelines:**
- Always use the agent before implementing from scratch
- Adapt discovered patterns to project-specific requirements
- Use for both complex features and simple API usage
- Validate documentation against current best practices

## Research-Driven Development Standards

### Before Any Implementation

**Research checklist:**

- [ ] Use @agent-context7-docs-searcher to research implementation approach
- [ ] Research best practices for relevant technologies
- [ ] Understand security implications
- [ ] Check for common pitfalls or antipatterns

### Using @agent-context7-docs-searcher

**When to use:**
- Before implementing any new feature or functionality
- When working with unfamiliar libraries or frameworks
- To find the most current best practices
- To research proper API usage and patterns

**How to invoke:**
```bash
@agent-context7-docs-searcher "Research [specific topic/library/pattern]"
```

**Example invocations:**
- `@agent-context7-docs-searcher "Research TypeScript generics and type constraints"`
- `@agent-context7-docs-searcher "Find best practices for React state management"`
- `@agent-context7-docs-searcher "Research Node.js async error handling patterns"`
- `@agent-context7-docs-searcher "Find PostgreSQL connection pooling implementation"`

### Knowledge Source Prioritization

**Query Strategy:**
- Start with broad architectural queries, narrow to specific implementation
- Use @agent-context7-docs-searcher for both strategic decisions and tactical "how-to" questions
- Request cross-referencing of multiple documentation sources for validation
- Use focused topic queries for targeted results

## Quality Assurance Integration

### Code Operations Standards

**Use Serena MCP for ALL code operations:**
- [ ] All code searches performed with Serena MCP tools
- [ ] All code edits made with Serena symbol operations
- [ ] Traditional tools (grep, sed, awk) used ONLY as fallback
- [ ] Memory management for persistent project knowledge

### Research Validation

**Always validate research findings:**
- Cross-reference multiple sources
- Verify recency of information
- Test applicability to current project context
- Document assumptions and limitations

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
ALWAYS use @agent-context7-docs-searcher BEFORE writing any code.
ALWAYS use Serena MCP for code operations, traditional tools as fallback only.
ALWAYS use @agent-context7-docs-searcher for ALL documentation research.