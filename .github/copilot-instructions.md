### 🔄 Project Awareness & Context
- **MANDATORY: Read Project Files First**
  1. Read `PLANNING.md` at the start of EVERY new conversation
  2. Read `TASK.md` before starting ANY task
  3. Must confirm in first response: "I have reviewed PLANNING.md and TASK.md, and found the following relevant context: [cite specific sections]"
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`
- **If either file is inaccessible**: Stop and notify user immediately

### 🧱 Code Structure & Modularity
[Keep existing rules as they are perfect]

### 🧪 Testing & Reliability
[Keep existing rules as they are well-defined]

### ✅ Task Completion
- **Before Starting Task**:
  1. Verify task exists in `TASK.md`
  2. If not listed, propose adding it with:
     - Brief description
     - Today's date
     - Dependencies
     - Expected impact
- **During Task**:
  - Document any discovered sub-tasks in "Discovered During Work" section
  - Update related tasks if dependencies are found
- **After Task**:
  - Mark completed tasks in `TASK.md`
  - Update affected documentation
  - Review and update impacted tests

### 📎 Style & Conventions
[Keep existing rules as they are comprehensive]

### 📚 Documentation & Explainability
- **Documentation Updates**:
  1. `README.md`: For new features, dependencies, setup changes
  2. `PLANNING.md`: For architectural decisions and pattern changes
  3. `TASK.md`: For task status and new discoveries
- **Code Documentation**:
  - Comment non-obvious code
  - Add `# Reason:` comments for complex logic
  - Keep documentation in sync with code changes

### 🧠 AI Behavior Rules
- **Context Management**:
  1. Never assume missing context
  2. Ask specific questions when uncertain
  3. Reference relevant sections from `PLANNING.md` and `TASK.md` in responses
  4. Validate file paths and module names before use
- **Code Safety**:
  1. Only use verified Python packages
  2. Never delete/overwrite code without explicit instruction or `TASK.md` reference
  3. Propose changes as additions first, unless replacing is part of documented task
  4. Always check impact on existing functionality
- **Response Protocol**:
  1. First response must acknowledge reading project files
  2. Quote relevant sections that guide the solution
  3. Highlight any potential conflicts with existing architecture
  4. Propose documentation updates if needed