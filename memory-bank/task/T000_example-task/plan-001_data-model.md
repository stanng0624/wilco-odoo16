# PLAN-001: Data Model Design

## Parent Task
- **Task Folder**: T000_example-task
- **Task Tracking**: [task.md](./task.md)
- **Main Plan**: [plan.md](./plan.md)
- **Related Plans**: 
  - [UI/UX Design](./plan-002_ui-design.md)

## Purpose
This detailed plan demonstrates how to document database schema design and data model specifications. It shows the level of detail appropriate for a plan-XXX breakdown document.

In a real project, this would contain:
- Entity-relationship diagrams
- Field definitions and constraints
- Database migration scripts
- ORM model specifications

## Overview
Example data model for a hypothetical feature showing:
- Table structure design
- Field types and constraints
- Relationships between entities
- Indexes and performance considerations

## Detailed Specifications

### Model 1: ExampleModel
**Purpose**: Main entity for the example feature

**Fields**:
```python
class ExampleModel(models.Model):
    _name = 'example.model'
    _description = 'Example Model'
    
    name = fields.Char(
        string='Name',
        required=True,
        index=True
    )
    
    description = fields.Text(
        string='Description'
    )
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], default='draft', required=True)
    
    created_date = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True
    )
```

### Model 2: ExampleLine
**Purpose**: Related line items for the main entity

**Fields**:
```python
class ExampleLine(models.Model):
    _name = 'example.line'
    _description = 'Example Line Item'
    
    parent_id = fields.Many2one(
        'example.model',
        string='Parent',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    value = fields.Float(
        string='Value',
        digits=(16, 2)
    )
```

## Implementation Details

### Database Tables
```sql
-- Example SQL for reference
CREATE TABLE example_model (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    created_date TIMESTAMP DEFAULT NOW(),
    create_uid INTEGER,
    write_uid INTEGER,
    create_date TIMESTAMP,
    write_date TIMESTAMP
);

CREATE INDEX idx_example_model_name ON example_model(name);
CREATE INDEX idx_example_model_status ON example_model(status);
```

### ORM Relationships
- **One-to-Many**: ExampleModel → ExampleLine
- **Many-to-One**: ExampleLine → ExampleModel

### Constraints
- `name` must be unique per company
- `status` cannot be null
- `parent_id` must reference valid ExampleModel
- Line items cascade delete with parent

## Integration Points
- **account.move**: Links to accounting entries (if financial feature)
- **project.project**: Associates with projects (if project-related)
- **res.partner**: Links to customers/vendors (if partner-related)

## Testing Strategy

### Unit Tests
```python
def test_create_example_model(self):
    """Test creating example model record"""
    model = self.env['example.model'].create({
        'name': 'Test Model',
        'description': 'Test Description'
    })
    self.assertEqual(model.status, 'draft')
    self.assertTrue(model.created_date)

def test_cascade_delete(self):
    """Test line items are deleted with parent"""
    model = self.create_test_model()
    line = self.env['example.line'].create({
        'parent_id': model.id,
        'value': 100.00
    })
    model.unlink()
    # Verify line is deleted
    self.assertFalse(self.env['example.line'].search([('id', '=', line.id)]))
```

### Integration Tests
- Test creation from UI
- Test data import/export
- Test relationship integrity
- Test performance with large datasets

## Performance Considerations
- Index on `name` for fast lookup
- Index on `status` for filtered views
- Cascade delete optimized for batch operations
- Computed fields cached appropriately

## Security Considerations
- Access control via `ir.model.access.csv`
- Record rules for multi-company scenarios
- Field-level security for sensitive data
- Audit trail via create/write tracking

## Migration Strategy
```python
def migrate(cr, version):
    """Migration script for existing data"""
    if not version:
        return
    
    # Add new fields
    cr.execute("""
        ALTER TABLE example_model 
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft'
    """)
    
    # Update existing records
    cr.execute("""
        UPDATE example_model 
        SET status = 'active' 
        WHERE status IS NULL
    """)
```

## References
- [Odoo ORM Documentation](https://www.odoo.com/documentation/16.0/developer/reference/backend/orm.html)
- [PostgreSQL Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [Main Plan](./plan.md)
- [UI Design Plan](./plan-002_ui-design.md)

## Notes
This is an example showing appropriate detail level for a data model plan. Real plans should:
- Include actual field definitions for your feature
- Document all relationships and constraints
- Provide migration scripts for database changes
- Include comprehensive test coverage
- Consider performance implications

**Remember**: Update this document as the data model evolves during implementation!
