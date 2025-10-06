### 🔄 Project Awareness & Context
- **MANDATORY: Read Memory Bank Files First**
  1. Read `memory-bank/systemPatterns.md` at the start of EVERY new conversation for architecture context
  2. Read `memory-bank/tasks.md` before starting ANY task for current priorities and history
  3. Read `memory-bank/productContext.md` for business domain understanding
  4. Read `memory-bank/techContext.md` for technical implementation details
  5. Must confirm in first response: "I have reviewed the Memory Bank and found the following relevant context: [cite specific sections from relevant memory-bank/*.md files]"
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `memory-bank/systemPatterns.md`
- **If any Memory Bank file is inaccessible**: Stop and notify user immediately

### 🧱 Code Structure & Modularity
- **Follow Wilco Project Patterns** (defined in `memory-bank/systemPatterns.md`):
  - Use `wilco_` prefix for custom fields and methods
  - Extend existing Odoo models where possible (project.project, account.analytic.account)
  - Maintain analytic distribution consistency across all financial transactions
  - Follow established utility module patterns (External Identifier Utility)
- **Respect Model Relationships** (documented in `memory-bank/techContext.md`):
  - Project-based security and data isolation
  - Automatic analytic distribution from sales/purchase orders
  - Financial KPI computation patterns

### 🐍 Environment Management
- **MANDATORY: Use Conda Virtual Environment**:
  - **Environment Name**: `wilco-odoo16`
  - **ALL terminal commands** MUST be executed within the conda environment
  - **Command Format**: Prefix all Python/Odoo commands with `conda run -n wilco-odoo16`
  - **Examples**:
    - ✅ `conda run -n wilco-odoo16 python odoo-bin --help`
    - ✅ `conda run -n wilco-odoo16 pip install <package>`
    - ✅ `conda run -n wilco-odoo16 ./odoo-bin -c conf/odoo16-macos.conf`
    - ❌ `python odoo-bin --help` (NEVER use without conda)
    - ❌ `pip install <package>` (NEVER use without conda)
- **Environment Activation**: 
  - When running interactive sessions, first activate: `conda activate wilco-odoo16`
  - For single commands, use: `conda run -n wilco-odoo16 <command>`
- **Package Management**:
  - Always install Python packages using: `conda run -n wilco-odoo16 pip install <package>`
  - Check installed packages with: `conda run -n wilco-odoo16 pip list`

### 🧪 Testing & Reliability
- **Test Integration Points**:
  - Verify analytic distribution propagation
  - Test project-based financial calculations
  - Validate security and access controls
  - Check business workflow completeness
- **Follow Testing Patterns** from `memory-bank/systemPatterns.md`

### ✅ Task Completion
- **Before Starting Task**:
  1. Verify task exists in `memory-bank/tasks.md`
  2. Check for related historical tasks in the same file
  3. If not listed, propose adding it with:
     - Brief description
     - Today's date
     - Dependencies from existing Memory Bank context
     - Expected impact
- **During Task**:
  - Document any discovered sub-tasks in "Discovered During Work" section of `memory-bank/tasks.md`
  - Update related tasks if dependencies are found
  - Reference existing patterns from `memory-bank/systemPatterns.md`
- **After Task**:
  - Mark completed tasks in `memory-bank/tasks.md`
  - Update `memory-bank/progress.md` with implementation status
  - Update `memory-bank/activeContext.md` with current focus
  - Review and update impacted documentation in relevant Memory Bank files

### 📎 Style & Conventions
- **Follow Wilco Naming Conventions** (from `memory-bank/systemPatterns.md`):
  - Standard Fields: Keep Odoo naming conventions
  - Extended Fields: Use `wilco_` prefix (e.g., `wilco_project_name`)
  - Computation Methods: Use `_wilco_compute_` prefix
  - Action Methods: Use `wilco_action_` prefix
- **Code Organization**:
  - Separate business logic into clear methods
  - Use computed fields with proper dependencies
  - Maintain project-based security patterns
  - Document model relationships in method comments

### 📚 Documentation & Explainability
- **Memory Bank Updates**:
  1. `memory-bank/tasks.md`: For task status, discoveries, and new requirements
  2. `memory-bank/systemPatterns.md`: For architectural decisions and pattern changes
  3. `memory-bank/techContext.md`: For technical implementation updates
  4. `memory-bank/productContext.md`: For business workflow changes
  5. `memory-bank/progress.md`: For implementation status and milestones
  6. `memory-bank/activeContext.md`: For current session focus and priorities
- **Code Documentation**:
  - Comment non-obvious code following Wilco patterns
  - Add `# Reason:` comments for complex business logic
  - Reference Memory Bank sections for architectural decisions
  - Keep documentation in sync with Memory Bank updates

### 🧠 AI Behavior Rules
- **Context Management**:
  1. Never assume missing context - always reference Memory Bank
  2. Ask specific questions when Memory Bank doesn't provide clarity
  3. Reference relevant sections from Memory Bank files in responses
  4. Validate file paths and module names against `memory-bank/systemPatterns.md`
- **Code Safety**:
  1. Only use patterns verified in `memory-bank/systemPatterns.md`
  2. Never delete/overwrite code without explicit instruction or `memory-bank/tasks.md` reference
  3. Propose changes as additions first, unless replacing is part of documented task
  4. Always check impact on existing functionality using Memory Bank context
- **Response Protocol**:
  1. First response must acknowledge reading relevant Memory Bank files
  2. Quote relevant sections that guide the solution
  3. Highlight any potential conflicts with existing architecture from `memory-bank/systemPatterns.md`
  4. Propose Memory Bank updates if new patterns or tasks are discovered

### 🏗️ Memory Bank Integration
- **Single Source of Truth**: All project documentation lives in Memory Bank
- **File Purpose Understanding**:
  - `tasks.md`: Current priorities, historical context, bug tracking
  - `systemPatterns.md`: Architecture, naming conventions, development guidelines
  - `productContext.md`: Business workflows and domain knowledge
  - `techContext.md`: Data structures, integration patterns, security
  - `progress.md`: Implementation tracking and milestones
  - `activeContext.md`: Current session state and focus
  - `projectbrief.md`: High-level project overview
- **Consistency Requirement**: All responses must align with Memory Bank content and update it when new information is discovered
