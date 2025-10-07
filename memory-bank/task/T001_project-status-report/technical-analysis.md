# Technical Analysis: Project Status Report

**Task**: T001  
**Created**: October 6, 2025  
**Analyst**: GitHub Copilot

---

## 📊 Data Model Analysis

### Existing Model Relationships

```
project.project (Core Entity)
    ↓ (wilco_project_id)
    ├─→ sale.order
    │   ├─ name (Order Number)
    │   ├─ date_order
    │   ├─ partner_id (Customer)
    │   ├─ amount_total
    │   ├─ wilco_amount_invoiced_total
    │   ├─ wilco_amount_invoice_remainder
    │   ├─ wilco_amount_settled_total
    │   └─ state
    │
    ├─→ account.move (Customer Invoices)
    │   WHERE move_type = 'out_invoice'
    │   ├─ name (Invoice Number)
    │   ├─ invoice_date
    │   ├─ partner_id (Customer)
    │   ├─ amount_total
    │   ├─ wilco_amount_settled_total
    │   ├─ amount_residual
    │   ├─ wilco_payment_dates
    │   └─ payment_state
    │
    └─→ account.move (Vendor Bills)
        WHERE move_type = 'in_invoice'
        ├─ name (Bill Number)
        ├─ invoice_date
        ├─ partner_id (Vendor)
        ├─ amount_total
        ├─ wilco_amount_settled_total
        ├─ amount_residual
        ├─ wilco_payment_dates
        └─ payment_state
```

### Field Analysis

#### Project Fields (Available)
- ✅ `name` - Project Number
- ✅ `wilco_project_name` - Project Name
- ✅ `stage_id` - Project Stage
- ✅ `last_update_status` - Status (On Track, At Risk, etc.)
- ✅ `wilco_date_award` - Award Date
- ✅ `analytic_account_id` - Link to financial data
- ✅ `analytic_account_balance` - Profit calculation

#### Sales Order Fields (Verified)
From `models/sale_order.py`:
- ✅ `wilco_project_id` - Many2one to project.project (Line 27-33)
- ✅ `wilco_amount_invoiced_total` - Computed field (Line 52-55)
- ✅ `wilco_amount_invoice_remainder` - Computed field (Line 56-59)
- ✅ `wilco_amount_settled_total` - Computed field (Line 68-71)
- ✅ `wilco_amount_residual_total` - Computed field (Line 72-75)

#### Invoice/Bill Fields (Verified)
From `models/account_move.py`:
- ✅ `wilco_project_id` - Many2one to project.project (Line 14-18)
- ✅ `wilco_payment_dates` - Computed, stored (Line 7)
- ✅ `wilco_amount_settled_total` - Computed field (Line 26)
- ✅ Standard Odoo fields: amount_total, amount_residual, payment_state

---

## 🔍 Query Performance Analysis

### Data Retrieval Queries

#### Query 1: Sales Orders
```python
sales_orders = env['sale.order'].search([
    ('wilco_project_id', '=', project_id)
], order='date_order desc')
```
- **Index**: `wilco_project_id` has `index=True` (verified in model)
- **Performance**: Good - indexed field with simple equality
- **Expected Volume**: 1-50 records per project (typical)

#### Query 2: Customer Invoices
```python
customer_invoices = env['account.move'].search([
    ('wilco_project_id', '=', project_id),
    ('move_type', '=', 'out_invoice')
], order='invoice_date desc, name desc')
```
- **Index**: `wilco_project_id` has `index=True` (verified)
- **Performance**: Good - indexed field + simple filter
- **Expected Volume**: 5-100 records per project

#### Query 3: Vendor Bills
```python
vendor_bills = env['account.move'].search([
    ('wilco_project_id', '=', project_id),
    ('move_type', '=', 'in_invoice')
], order='invoice_date desc, name desc')
```
- **Index**: Same as Query 2
- **Performance**: Good
- **Expected Volume**: 5-100 records per project

### Performance Estimates
- **Small Project** (10 total records): < 0.5 seconds
- **Medium Project** (50 total records): < 1 second
- **Large Project** (200 total records): < 2 seconds
- **Very Large Project** (500+ records): 2-5 seconds

**Conclusion**: Performance is acceptable. No optimization needed initially.

---

## 🏗️ Architecture Comparison

### Pattern Analysis: Customer Invoice Summary vs Project Status Report

| Aspect | Customer Invoice Summary | Project Status Report |
|--------|-------------------------|----------------------|
| **Purpose** | Period-based invoice aggregation | Project-based transaction listing |
| **Data Model** | Permanent model (stored data) | Transient wizard (no storage) |
| **Data Scope** | All customers, filtered by period | Single project, all transactions |
| **Complexity** | High (aggregation, grouping) | Medium (direct listing) |
| **User Input** | Multiple filters, grouping options | Project selection only |
| **Output** | Tree view + breakdowns + PDF | Direct PDF report |

### Recommended Approach

**Decision**: Use **simpler wizard pattern** (like vendor bill summary)

**Rationale**:
1. No need for permanent data storage
2. No aggregation required (direct listing)
3. Single project context (simpler than multi-entity)
4. Faster implementation and maintenance
5. Lower complexity = fewer bugs

---

## 🎨 UI/UX Design Analysis

### Report Access Point

**Location**: Project form view stat buttons area

**Comparison with Existing Buttons**:
```xml
<!-- Existing: Analytic Lines button -->
<button class="oe_stat_button" type="object"
        name="wilco_action_view_analytic_lines"
        icon="fa-usd">
    <div class="o_form_field o_stat_info">
        <span class="o_stat_value">
            <field name="analytic_account_balance"/>
        </span>
        <span class="o_stat_text">Profit</span>
    </div>
</button>

<!-- Proposed: Status Report button -->
<button class="oe_stat_button" type="action"
        name="%(action_wilco_project_status_report_wizard)d"
        icon="fa-file-text-o">
    <div class="o_form_field o_stat_info">
        <span class="o_stat_text">Status</span>
        <span class="o_stat_text">Report</span>
    </div>
</button>
```

**Icon Choice**: `fa-file-text-o` (document/report icon)  
**Placement**: After financial stat buttons, before task-related buttons

---

## 📄 Report Layout Analysis

### Page Structure

```
┌─────────────────────────────────────────────┐
│ COMPANY HEADER (Standard Odoo)              │
├─────────────────────────────────────────────┤
│ Project Status Report                       │
│                                             │
│ Project Information                         │
│ ┌───────────────┬───────────────────────┐  │
│ │ Number: XXX   │ Award Date: YYYY-MM-DD │ │
│ │ Name: XXXXXX  │ Status: On Track       │ │
│ │ Stage: Active │ Report Date: Today     │ │
│ └───────────────┴───────────────────────┘  │
│                                             │
│ Sales Orders                                │
│ ┌─────────────────────────────────────────┐│
│ │ Order# │ Date │ Customer │ Amt │ Status ││
│ │────────┼──────┼──────────┼─────┼────────││
│ │ SO001  │ ...  │ Cust A   │ 100 │ Sale   ││
│ │ Total: │      │          │ 100 │        ││
│ └─────────────────────────────────────────┘│
│                                             │
│ Customer Invoices                           │
│ ┌─────────────────────────────────────────┐│
│ │ Inv# │ Date │ Customer │ Amt │ Settled  ││
│ │──────┼──────┼──────────┼─────┼──────────││
│ │ INV1 │ ...  │ Cust A   │ 100 │ 100      ││
│ └─────────────────────────────────────────┘│
│                                             │
│ Vendor Bills                                │
│ ┌─────────────────────────────────────────┐│
│ │ Bill# │ Date │ Vendor │ Amt │ Settled   ││
│ └─────────────────────────────────────────┘│
│                                             │
├─────────────────────────────────────────────┤
│ COMPANY FOOTER (Standard Odoo)              │
└─────────────────────────────────────────────┘
```

### Styling References

**Base Template**: Follow `sale_report_template.xml` pattern
- Bootstrap 4 classes for responsive layout
- Odoo standard table styling
- Proper monetary field formatting
- Date format consistency

**Color Scheme**: Odoo default (no custom colors needed)

---

## 🔐 Security Analysis

### Access Control Requirements

#### Required Groups
- **Project Access**: `project.group_project_user` (minimum)
- **Sales Access**: `sales_team.group_sale_salesman` (for SO data)
- **Invoice Access**: `account.group_account_readonly` (for financial data)

#### Security Approach
1. **Wizard Access**: Inherit project security (no additional rules needed)
2. **Data Filtering**: Use Odoo's built-in record rules
3. **Report Action**: Respect existing model permissions

#### Record-Level Security
```python
# Existing security automatically applied via search()
sales_orders = env['sale.order'].search([...])  # Applies ir.rule filters
invoices = env['account.move'].search([...])    # Applies ir.rule filters
```

**Conclusion**: No custom security rules needed. Existing Odoo security sufficient.

---

## 💾 Data Consistency Checks

### Potential Data Issues

#### Issue 1: Orphaned Records
- **Scenario**: Project deleted but transactions remain
- **Current Behavior**: `wilco_project_id` would be False
- **Solution**: Query already filters by project_id, so excluded automatically

#### Issue 2: Draft/Cancelled Records
- **Scenario**: Should drafts appear in report?
- **Decision**: Show ALL states, add status column
- **Rationale**: Provides complete picture, user can interpret

#### Issue 3: Multi-company
- **Scenario**: Project in Company A, invoice in Company B
- **Current Behavior**: Odoo's company rules prevent cross-company data
- **Solution**: No additional handling needed

#### Issue 4: Archived Records
- **Scenario**: Archived sales orders/invoices
- **Decision**: Include archived records (they're historical data)
- **Implementation**: No `active=True` filter

---

## 🧪 Test Data Requirements

### Test Scenario 1: Comprehensive Project
```python
project_001 = {
    'name': 'PRJ001',
    'wilco_project_name': 'Test Project Alpha',
    'stage_id': 'Active',
    'sales_orders': 3,      # 3 SOs in different states
    'customer_invoices': 5, # 5 invoices, some paid, some unpaid
    'vendor_bills': 4,      # 4 bills, various payment states
}
```

### Test Scenario 2: Empty Project
```python
project_002 = {
    'name': 'PRJ002',
    'wilco_project_name': 'Empty Project',
    'sales_orders': 0,
    'customer_invoices': 0,
    'vendor_bills': 0,
}
```

### Test Scenario 3: Single Type
```python
project_003 = {
    'name': 'PRJ003',
    'wilco_project_name': 'Sales Only Project',
    'sales_orders': 2,
    'customer_invoices': 0,
    'vendor_bills': 0,
}
```

---

## 📈 Aggregation Requirements

### Required Calculations

#### Sales Orders Section
- ✅ Total Amount: `sum(sale_order.amount_total)`
- ✅ Total Invoiced: `sum(sale_order.wilco_amount_invoiced_total)`
- ✅ Total Balance: `sum(sale_order.wilco_amount_invoice_remainder)`

#### Customer Invoices Section
- ✅ Total Amount: `sum(account_move.amount_total)`
- ✅ Total Settled: `sum(account_move.wilco_amount_settled_total)`
- ✅ Total Due: `sum(account_move.amount_residual)`

#### Vendor Bills Section
- ✅ Total Amount: `sum(account_move.amount_total)`
- ✅ Total Settled: `sum(account_move.wilco_amount_settled_total)`
- ✅ Total Due: `sum(account_move.amount_residual)`

### Implementation Method
Use QWeb `t-esc` with Python sum():
```xml
<t t-esc="sum(sales_orders.mapped('amount_total'))"/>
```

**Performance**: O(n) for each total, acceptable for report volume

---

## 🔄 Integration Points

### Existing Systems

#### 1. Project Module
- **Integration**: Button on project form view
- **Data**: Project master data
- **Security**: Inherits project access rules

#### 2. Sales Module
- **Integration**: Read sales order data
- **Fields Used**: All `wilco_*` computed fields
- **No Modifications**: Read-only access

#### 3. Accounting Module
- **Integration**: Read invoice/bill data
- **Fields Used**: Standard + `wilco_*` fields
- **No Modifications**: Read-only access

#### 4. Reporting Framework
- **Integration**: Use QWeb PDF engine
- **Template Base**: Follow existing report patterns
- **Output**: PDF generation via `ir.actions.report`

### No Breaking Changes
- ✅ Read-only operations
- ✅ No schema modifications
- ✅ No workflow changes
- ✅ Optional feature (existing flows unaffected)

---

## 🎯 Implementation Complexity Assessment

### Complexity Matrix

| Component | Complexity | Effort | Risk |
|-----------|-----------|--------|------|
| Wizard Model | Low | 2h | Low |
| Data Collection | Low | 1h | Low |
| QWeb Template | Medium | 3h | Medium |
| Report Action | Low | 1h | Low |
| View Integration | Low | 1h | Low |
| Testing | Medium | 2h | Low |

**Total Estimated Effort**: 10 hours  
**Overall Complexity**: **L3-High** (due to template complexity)  
**Risk Level**: **Low** (standard Odoo patterns)

---

## ✅ Technical Validation

### Feasibility Checks

- ✅ **Data Availability**: All required fields exist in models
- ✅ **Performance**: Queries are indexed and efficient
- ✅ **Security**: Existing access controls sufficient
- ✅ **Compatibility**: Uses standard Odoo 16 patterns
- ✅ **Maintainability**: Follows Wilco conventions
- ✅ **Scalability**: Handles expected data volumes
- ✅ **No Dependencies**: No new modules required

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Large dataset performance | Low | Medium | Add pagination if needed |
| QWeb rendering errors | Low | Low | Test thoroughly, follow patterns |
| Security gaps | Very Low | High | Use standard Odoo security |
| Multi-currency issues | Medium | Low | Display in transaction currency |

**Overall Risk**: **LOW** - Standard implementation with proven patterns

---

## 🚀 Ready for Implementation

**Analysis Conclusion**: ✅ **APPROVED FOR IMPLEMENTATION**

All technical requirements validated:
- ✅ Data model supports requirements
- ✅ Performance is acceptable
- ✅ Security is adequate
- ✅ Integration points identified
- ✅ Risk is low
- ✅ Effort is reasonable

**Recommended Next Mode**: **IMPLEMENT MODE**

No creative phases required - standard implementation using existing patterns.
