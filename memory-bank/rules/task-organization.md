# TASK ORGANIZATION RULES

> **Last Updated**: October 6, 2025  
> **Version**: 2.0  
> **Status**: Active

## 📁 **FOLDER STRUCTURE**

```
memory-bank/
└── task/
    ├── T001_customer-invoice-summary/
    │   ├── task.md                    # Main task tracking file
    │   ├── plan.md                    # Main implementation plan
    │   ├── plan-001_data-model.md     # Detailed data model design
    │   ├── plan-002_ui-views.md       # UI/UX design details
    │   └── plan-003_reporting.md      # Reporting implementation
    │
    ├── T002_vendor-bill-summary/
    │   ├── task.md
    │   ├── plan.md
    │   └── plan-001_wizard-logic.md
    │
    ├── T003_memory-bank-migration/
    │   ├── task.md
    │   └── plan.md
    │
    └── [TXXX_short-name]/
        ├── task.md                     # Required: Task tracking
        ├── plan.md                     # Optional: Main plan
        └── plan-XXX_*.md               # Optional: Detailed breakdowns
```

---

## 🎯 **NAMING CONVENTIONS**

### Task Folders
- **Format**: `TXXX_short-name`
- **Pattern**: `T[3-digit-number]_[kebab-case-name]`
- **Requirements**:
  - Zero-padded 3-digit number (T001, T002, ..., T999)
  - Short, descriptive kebab-case name
  - Keep folder name under 50 characters
- **Examples**: 
  - ✅ `T001_customer-invoice-summary`
  - ✅ `T002_vendor-bill-summary`
  - ✅ `T042_project-profitability`
  - ❌ `task-001` (wrong prefix)
  - ❌ `T42_project` (missing zero-padding)
  - ❌ `T001_Customer_Invoice` (not kebab-case)

### Task Files (Always Required)
- **Filename**: `task.md` (standardized, must exist)
- **Purpose**: Track task status, requirements, progress, completion criteria
- **Content Sections**: Status, priority, dependencies, progress log, results
- **Location**: Root of task folder

### Plan Files (Optional)

#### Main Plan
- **Filename**: `plan.md` (standardized)
- **Purpose**: High-level implementation strategy and approach
- **When to Create**: For tasks with complexity ≥ L2-Medium
- **When to Skip**: Simple tasks (L1) that don't need detailed planning

#### Detailed Plan Breakdowns
- **Filename Pattern**: `plan-[3-digit-number]_[kebab-case-description].md`
- **Purpose**: Deep-dive into specific aspects of implementation
- **Numbering**: Sequential within each task folder (starts from 001)
- **Examples**:
  - ✅ `plan-001_data-model.md`
  - ✅ `plan-002_ui-design.md`
  - ✅ `plan-003_integration.md`
  - ✅ `plan-004_performance-optimization.md`
  - ❌ `plan-1_model.md` (missing zero-padding)
  - ❌ `data-model-plan.md` (wrong format)

---

## 🔢 **ID ASSIGNMENT SYSTEM**

### Task Numbers
- **Current Next ID**: T041
- **Format**: Zero-padded 3 digits (T001, T002, ..., T999)
- **Scope**: Unique across entire project lifecycle
- **Assignment Rule**: Increment sequentially from last assigned
- **Do Not**: Reuse IDs even if tasks are deleted

### Plan Breakdown Numbers  
- **Format**: `plan-XXX_name.md` where XXX is sequential
- **Scope**: Unique within each task folder only
- **Start**: Always from 001 within each new task
- **Example**: 
  - Task T042 can have: plan-001, plan-002, plan-003
  - Task T043 can also have: plan-001, plan-002, plan-003
- **Increment**: Add new numbers as needed within task

---

## 📝 **FILE CONTENT TEMPLATES**

### task.md Template

```markdown
# TASK-XXX: [Task Title]

## Overview
- **ID**: TXXX
- **Status**: [Not Started | In Progress | Blocked | Completed | Archived]
- **Priority**: [P0-Critical | P1-High | P2-Medium | P3-Low]
- **Created**: YYYY-MM-DD
- **Updated**: YYYY-MM-DD
- **Assignee**: [Name/Team]
- **Complexity**: [L1-Simple | L2-Medium | L3-Complex | L4-Critical]

## Description
[Clear, concise description of the task objective and context]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

## Dependencies
- **Blocks**: [List of task IDs this task blocks]
- **Blocked By**: [List of task IDs blocking this task]
- **Related**: [Related task IDs for reference]

## Plan Documents
- [Main Plan](./plan.md)
- [Data Model Design](./plan-001_data-model.md)
- [UI Design](./plan-002_ui-design.md)

## Metadata
- **Category**: [Feature | Bug | Enhancement | Maintenance | Migration]
- **Module**: [wilco_project | accounting | reporting | core]
- **Impact**: [High | Medium | Low]
- **Estimated Effort**: [Hours/Days]

## Progress Log

### YYYY-MM-DD - [Activity Summary]
- Activity details
- Decisions made
- Blockers encountered

### YYYY-MM-DD - [Activity Summary]
- Next activity
- Updates

## Completion Criteria
- [ ] All requirements implemented
- [ ] Unit tests passing
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed to target environment

## Results/Deliverables
[Final outcomes, links to commits, deployed features, documentation]

## Notes
[Any additional context, lessons learned, or future considerations]
```

### plan.md Template

```markdown
# PLAN: [Task Title]

## Overview
- **Task**: TXXX_short-name
- **Plan Version**: 1.0
- **Created**: YYYY-MM-DD
- **Updated**: YYYY-MM-DD

## Objectives
[What this plan aims to achieve - clear, measurable goals]

## Scope

### In Scope
- Feature/component 1
- Feature/component 2
- Integration point 1

### Out of Scope
- Future enhancement 1
- Alternative approach not chosen
- Dependencies handled by other tasks

## Detailed Plans
- [Data Model Design](./plan-001_data-model.md)
- [UI/UX Design](./plan-002_ui-design.md)
- [Integration Strategy](./plan-003_integration.md)

## Technical Approach

### Architecture Overview
[High-level architectural decisions and patterns]

### Technology Stack
- Framework/Library 1
- Tool/Service 2

### Key Design Decisions
1. **Decision**: [What was decided]
   - **Rationale**: [Why this approach]
   - **Alternatives Considered**: [What was not chosen]

## Implementation Phases

### Phase 1: [Foundation]
- Task 1.1
- Task 1.2
- **Deliverable**: [What's completed in this phase]

### Phase 2: [Development]
- Task 2.1
- Task 2.2
- **Deliverable**: [What's completed in this phase]

### Phase 3: [Integration & Testing]
- Task 3.1
- Task 3.2
- **Deliverable**: [What's completed in this phase]

## Success Metrics
- Metric 1: [Specific, measurable criterion]
- Metric 2: [Specific, measurable criterion]
- Metric 3: [Specific, measurable criterion]

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| Risk 1 | High | Medium | Mitigation approach |
| Risk 2 | Medium | Low | Mitigation approach |

## Testing Strategy
- Unit testing approach
- Integration testing requirements
- User acceptance testing criteria

## Timeline
- **Phase 1**: Start - End dates
- **Phase 2**: Start - End dates
- **Phase 3**: Start - End dates

## Resources
- Documentation links
- Reference implementations
- External dependencies
```

### plan-XXX_name.md Template

```markdown
# PLAN-XXX: [Specific Aspect Title]

## Parent Task
- **Task**: TXXX_short-name
- **Main Plan**: [plan.md](./plan.md)
- **Task Tracking**: [task.md](./task.md)

## Purpose
[Why this detailed plan is needed - what aspect of the main plan does it elaborate on]

## Overview
[Brief summary of this specific aspect]

## Detailed Specifications

### Component 1: [Name]
[Detailed technical specifications]

### Component 2: [Name]
[Detailed technical specifications]

## Implementation Details

### Code Structure
```python
# Example code structure or pseudocode
```

### Configuration
```yaml
# Configuration examples
```

### Data Models
[Entity relationships, field definitions, constraints]

## Integration Points
- System/module 1
- System/module 2

## Testing Strategy

### Unit Tests
- Test case 1
- Test case 2

### Integration Tests
- Test scenario 1
- Test scenario 2

## Performance Considerations
- Performance requirement 1
- Optimization strategy 1

## Security Considerations
- Security requirement 1
- Access control strategy

## References
- [Related Documentation](link)
- [External Resources](link)
- [Code Examples](link)

## Notes
[Additional context, alternatives considered, future enhancements]
```

---

## 🔗 **CROSS-REFERENCING RULES**

### 1. From tasks.md Index → Task Folders
```markdown
### Active Tasks
- [T041: Project Profitability Dashboard](./task/T041_project-profitability/task.md) - 🔄 In Progress
- [T042: Budget Analysis Report](./task/T042_budget-analysis/task.md) - ⏸️ Blocked

### Completed Tasks
- [T001: Customer Invoice Summary](./task/T001_customer-invoice-summary/task.md) - ✅ Completed (2025-06-15)
```

### 2. From task.md → Plan Documents (Relative Links)
```markdown
## Plan Documents
- [Main Implementation Plan](./plan.md)
- [Data Model Design](./plan-001_data-model.md)
- [UI/UX Design](./plan-002_ui-design.md)
- [Performance Optimization](./plan-003_performance.md)
```

### 3. From plan.md → Detailed Plans (Relative Links)
```markdown
## Detailed Plans
This plan is broken down into the following detailed specifications:
- [Data Model Design](./plan-001_data-model.md) - Database schema and ORM models
- [UI/UX Design](./plan-002_ui-design.md) - User interface and experience
- [Integration Strategy](./plan-003_integration.md) - Third-party integrations
```

### 4. From Detailed Plans → Parent Documents (Relative Links)
```markdown
## Parent Task
- **Task Folder**: T042_budget-analysis
- **Task Tracking**: [task.md](./task.md)
- **Main Plan**: [plan.md](./plan.md)
- **Related Plans**: 
  - [Data Model](./plan-001_data-model.md)
  - [Integration](./plan-003_integration.md)
```

### 5. Between Tasks (Relative from memory-bank/task/)
```markdown
## Dependencies
- **Blocks**: 
  - [T045: Financial Dashboard](../T045_financial-dashboard/task.md)
  - [T046: Reporting Engine](../T046_reporting-engine/task.md)
  
- **Blocked By**: 
  - [T008: Core Integration](../T008_core-integration/task.md) - Must complete API endpoints
  
- **Related**: 
  - [T012: User Authentication](../T012_user-auth/task.md) - Shares security patterns
```

---

## ✅ **TASK LIFECYCLE WORKFLOW**

### Creating New Task

1. **Determine Next ID**
   - Check `tasks.md` for current highest task number
   - Increment by 1 (e.g., if last is T040, next is T041)

2. **Create Task Folder**
   ```bash
   mkdir -p memory-bank/task/TXXX_short-name
   ```

3. **Create task.md**
   - Copy template from this document
   - Fill in Overview section with task details
   - Set Status to "Not Started"
   - Add requirements and dependencies

4. **Create plan.md (if needed)**
   - Only for tasks with complexity ≥ L2-Medium
   - Copy template and customize
   - Break down into phases if complex

5. **Create Detailed Plans (if needed)**
   - For complex tasks (L3, L4) that need deep-dive specs
   - Use `plan-001_`, `plan-002_` numbering
   - Link from main plan.md

6. **Update tasks.md Index**
   - Add entry in appropriate section (Active/Planned)
   - Include task ID, title, and link
   - Set initial status indicator

7. **Link Dependencies**
   - Update dependent tasks with references
   - Check for circular dependencies
   - Update blocked tasks list

### During Implementation

1. **Update Progress Log**
   - Add dated entries for significant activities
   - Document decisions and changes
   - Note blockers and resolutions

2. **Update Status**
   - Change from "Not Started" to "In Progress"
   - Update "Updated" date in Overview
   - Check off requirements as completed

3. **Create Additional Plans**
   - Add plan-XXX files as new aspects emerge
   - Update main plan.md to reference them
   - Keep numbering sequential

4. **Track Blockers**
   - Update "Blocked By" section if blocked
   - Change status to "Blocked" if necessary
   - Communicate with blocking task owners

5. **Update Dependencies**
   - If task scope changes, update dependent tasks
   - Add newly discovered related tasks
   - Keep cross-references current

### Completing Task

1. **Verify Completion Criteria**
   - ✅ Check all requirements completed
   - ✅ Verify all completion criteria met
   - ✅ Ensure deliverables documented

2. **Document Results**
   - Fill in Results/Deliverables section
   - Add links to commits, PRs, deployments
   - Note any deviations from plan

3. **Update Status**
   - Change status to "Completed"
   - Add completion date to Overview
   - Update final "Updated" timestamp

4. **Update tasks.md Index**
   - Move from Active to Completed section
   - Add ✅ indicator and completion date
   - Keep link active for reference

5. **Notify Dependent Tasks**
   - Update tasks that were blocked by this
   - Remove from "Blocked By" lists
   - Alert assignees of unblocked tasks

6. **Archive (Optional)**
   - For very old completed tasks, can change status to "Archived"
   - Keep folder structure intact for history
   - Maintain all links for reference

---

## 📊 **TASK CATEGORIZATION**

### Status Values
- **Not Started**: Task created but work hasn't begun
- **In Progress**: Active development/implementation
- **Blocked**: Waiting on dependencies or external factors
- **Completed**: All criteria met, deliverables done
- **Archived**: Old completed task, kept for reference

### Priority Levels
- **P0-Critical**: System down, blocking production, security issue
- **P1-High**: Important feature, affects users, tight deadline
- **P2-Medium**: Standard feature work, planned improvements
- **P3-Low**: Nice-to-have, future enhancements, cleanup

### Complexity Levels
- **L1-Simple**: < 4 hours, single file, no dependencies
- **L2-Medium**: 1-2 days, multiple files, few dependencies
- **L3-Complex**: 1-2 weeks, cross-module, many dependencies
- **L4-Critical**: > 2 weeks, architectural changes, high risk

### Categories
- **Feature**: New functionality or capability
- **Bug**: Fixing incorrect behavior
- **Enhancement**: Improving existing functionality
- **Maintenance**: Refactoring, cleanup, technical debt
- **Migration**: Data or system migration tasks

### Impact Levels
- **High**: Affects many users or critical workflows
- **Medium**: Affects specific user groups or features
- **Low**: Limited scope, optional improvements

---

## 🎯 **BENEFITS OF THIS STRUCTURE**

### Organization Benefits
1. **Self-Contained**: Each task folder is a complete unit with all related docs
2. **Scalable**: Can handle hundreds of tasks without structure breaking down
3. **Predictable**: Standard file names make navigation intuitive
4. **Flexible**: Can add detailed plans without reorganizing folders

### Development Benefits
1. **Clear Context**: Everything related to a task is in one place
2. **Easy Planning**: Break complex work into manageable plan documents
3. **Better Tracking**: Progress log and status in predictable location
4. **Reduced Coupling**: Plans live with tasks, not in separate tree

### Collaboration Benefits
1. **Easy Discovery**: Folder names and IDs make tasks findable
2. **Clear Dependencies**: Explicit linking between related tasks
3. **Better History**: All task evolution documented in one place
4. **Simple Reviews**: Reviewers know where to find specifications

### Maintenance Benefits
1. **Better Git**: Easier to track changes per task in diffs
2. **Simpler References**: Relative links within folder are stable
3. **Clean Structure**: No orphaned plans or broken cross-references
4. **Future-Proof**: Structure supports long-term project growth

---

## 🚨 **COMMON PITFALLS TO AVOID**

### ❌ Don't Do This
1. **Skip task.md**: Every folder must have task.md
2. **Reuse Task IDs**: Never reuse IDs, even for deleted tasks
3. **Inconsistent Naming**: Stick to TXXX_kebab-case format
4. **Orphaned Plans**: Don't create plans without linking from task.md
5. **Absolute Paths**: Use relative links within task folders
6. **No Zero-Padding**: Always use T001, not T1
7. **Mixed Cases**: Use kebab-case, not snake_case or camelCase
8. **Long Folder Names**: Keep task folder names under 50 chars
9. **Duplicate Plan Numbers**: Within a task, each plan-XXX must be unique
10. **Forget Index**: Always update tasks.md when creating tasks

### ✅ Do This Instead
1. **Always create task.md first**: It's the anchor for everything
2. **Increment sequentially**: T040 → T041 → T042
3. **Follow naming pattern**: `TXXX_short-kebab-case-name`
4. **Link from task.md**: Include plan documents in references
5. **Use relative links**: `./plan.md`, `../T008_core/task.md`
6. **Pad with zeros**: T001, T042, T999
7. **Use kebab-case**: `data-model`, not `data_model` or `dataModel`
8. **Be concise**: `T042_budget-report` not `T042_comprehensive-budget-analysis-report-system`
9. **Number sequentially**: plan-001, plan-002, plan-003 per task
10. **Update index immediately**: Add to tasks.md when creating folder

---

## 📚 **QUICK REFERENCE CHEATSHEET**

### Task Creation Checklist
```
□ Determine next task ID (check tasks.md)
□ Create folder: memory-bank/task/TXXX_name/
□ Create task.md from template
□ Create plan.md if complexity ≥ L2
□ Create plan-XXX files for complex tasks
□ Update tasks.md index
□ Link dependencies
□ Set initial status
```

### File Naming Quick Reference
```
✅ T001_customer-invoice-summary/task.md
✅ T042_project-profitability/plan.md
✅ T042_project-profitability/plan-001_data-model.md

❌ task-042/task.md
❌ T42_project/plan.md
❌ T042_Project_Profitability/plan_001.md
```

### Link Patterns Quick Reference
```markdown
# In tasks.md → task folder
[T042: Project Profitability](./task/T042_project-profitability/task.md)

# In task.md → plans (same folder)
[Main Plan](./plan.md)
[Data Model](./plan-001_data-model.md)

# In task.md → other tasks
[T008: Core Integration](../T008_core-integration/task.md)

# In plan-XXX.md → parent files (same folder)
[Task](./task.md)
[Main Plan](./plan.md)
```

---

## 🔄 **VERSION HISTORY**

### Version 2.0 (October 6, 2025)
- **Major Change**: Plans now live in task folders, not separate plan/ folder
- **Added**: Detailed plan breakdown support (plan-XXX files)
- **Added**: Comprehensive templates and examples
- **Added**: Lifecycle workflow documentation
- **Added**: Common pitfalls and best practices

### Version 1.0 (December 2024)
- Initial task organization structure
- Separate task/ and plan/ folders
- Basic task and plan templates
- Sequential ID system

---

## 📞 **SUPPORT & QUESTIONS**

If you're unsure about:
- Which task ID to use next → Check tasks.md for highest number
- Whether to create a plan → Create if complexity ≥ L2
- How to break down complex plans → Use plan-XXX files
- How to link between tasks → Use relative paths from task/ folder

**Remember**: When in doubt, follow the templates and examples in this document!
