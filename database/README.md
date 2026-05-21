# Database Schema

Ceramix AI ERP - PostgreSQL 14+ Schema (v6)

The schema is split into three files for manageability:

1. **schema_part1.sql** - Extensions, core tables (tenants through sales_invoices, sections 1-22)
2. **schema_part2.sql** - Sales items through webhooks (sections 22-43)
3. **schema_part3.sql** - Scheduled reports, remaining tables, RLS, triggers, indexes, materialized views, deferred FKs, and seed data (sections 44-50+)

## Execution Order

```bash
psql -d your_database -f database/schema_part1.sql
psql -d your_database -f database/schema_part2.sql
psql -d your_database -f database/schema_part3.sql
```

## Key Features

- Multi-tenant with UUID-based isolation
- Row Level Security (RLS) policies for tenant isolation
- Partitioned tables for audit logs, journal entries, AI logs, and system events
- Materialized views for treasury/account balances (no denormalized balance columns)
- Product price history tracking via triggers
- Double-entry accounting with debit/credit constraints
- Full soft-delete support with partial indexes
- Hierarchical product categories
- Credit notes with line items + debit notes for purchase adjustments
- Webhook delivery log with retry support
- Multi-recipient scheduled reports
- Conditional approval workflows with amount thresholds
