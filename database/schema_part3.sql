-- Part 3: Scheduled reports through Seed data (sections 44-50 + triggers, indexes, views, FKs, seeds)

-- ============================================================
-- 44. SCHEDULED REPORTS (multi-recipient)
-- ============================================================

CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    report_name VARCHAR(255) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scheduled_report_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL
);

-- ============================================================
-- 45. BACKGROUND JOBS (with error tracking)
-- ============================================================

CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    job_type VARCHAR(100) NOT NULL,
    payload JSONB,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- ============================================================
-- 46. API RATE LIMITING (tenant + user level)
-- ============================================================

CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 47. BUSINESS INTELLIGENCE
-- ============================================================

CREATE TABLE kpi_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    query TEXT NOT NULL,
    unit VARCHAR(30),
    target_value NUMERIC(14, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    kpi_id UUID REFERENCES kpi_definitions(id) ON DELETE CASCADE,
    widget_type VARCHAR(50),
    position INTEGER,
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 48. SYSTEM HEALTH & BACKUP
-- ============================================================

CREATE TABLE system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    value NUMERIC(14, 4),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE backup_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    size_bytes BIGINT,
    status VARCHAR(30),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE restore_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_id UUID REFERENCES backup_logs(id) ON DELETE SET NULL,
    status VARCHAR(30),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- ============================================================
-- 49. DATABASE MIGRATION TRACKING
-- ============================================================

CREATE TABLE schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    applied_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 50. DATA RETENTION (with tenant scope)
-- ============================================================

CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL,
    archive_strategy VARCHAR(30) DEFAULT 'soft_delete',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) + Template Policy
-- ============================================================

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;

-- Template RLS policies (tenant isolation)
CREATE POLICY tenant_isolation_customers ON customers USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_suppliers ON suppliers USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_products ON products USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_warehouses ON warehouses USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_sales_invoices ON sales_invoices USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_purchase_invoices ON purchase_invoices USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_payments ON payments USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_expenses ON expenses USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_accounts ON accounts USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_journal_entries ON journal_entries USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_notifications ON notifications USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_leads ON leads USING (tenant_id = current_setting('app.current_tenant')::UUID);
CREATE POLICY tenant_isolation_opportunities ON opportunities USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- inventory uses product's tenant via join; simpler policy via warehouse
CREATE POLICY tenant_isolation_inventory ON inventory USING (
    warehouse_id IN (SELECT id FROM warehouses WHERE tenant_id = current_setting('app.current_tenant')::UUID)
);

-- ============================================================
-- TRIGGERS (Auto-update updated_at)
-- ============================================================

CREATE TRIGGER trg_companies_updated_at BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_branches_updated_at BEFORE UPDATE ON branches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_warehouses_updated_at BEFORE UPDATE ON warehouses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_inventory_updated_at BEFORE UPDATE ON inventory FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_sales_invoices_updated_at BEFORE UPDATE ON sales_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_purchase_invoices_updated_at BEFORE UPDATE ON purchase_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_accounts_updated_at BEFORE UPDATE ON accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_settings_updated_at BEFORE UPDATE ON settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- PRODUCT PRICE HISTORY TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION log_product_price_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.sale_price <> NEW.sale_price OR OLD.purchase_price <> NEW.purchase_price THEN
        INSERT INTO product_price_history (
            product_id, old_sale_price, new_sale_price,
            old_purchase_price, new_purchase_price, changed_by
        ) VALUES (
            NEW.id, OLD.sale_price, NEW.sale_price,
            OLD.purchase_price, NEW.purchase_price, NEW.updated_by
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_product_price_history
AFTER UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION log_product_price_change();

-- ============================================================
-- INDEXES
-- ============================================================

-- Tenants & Companies
CREATE INDEX idx_companies_tenant ON companies(tenant_id);
CREATE INDEX idx_branches_tenant ON branches(tenant_id);
CREATE INDEX idx_branches_company ON branches(company_id);

-- Currency
CREATE INDEX idx_exchange_rates_pair ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_date ON exchange_rates(rate_date);

-- Users
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_branch ON users(branch_id);

-- Sessions & API Keys
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- CRM
CREATE INDEX idx_customers_tenant ON customers(tenant_id);
CREATE INDEX idx_customers_company ON customers(company_id);
CREATE INDEX idx_customers_name ON customers(full_name);
CREATE INDEX idx_suppliers_tenant ON suppliers(tenant_id);
CREATE INDEX idx_suppliers_company ON suppliers(company_id);
CREATE INDEX idx_suppliers_name ON suppliers(company_name);

-- CRM Pipeline
CREATE INDEX idx_leads_tenant ON leads(tenant_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_opportunities_tenant ON opportunities(tenant_id);
CREATE INDEX idx_opportunities_stage ON opportunities(stage);
CREATE INDEX idx_activities_entity ON activities(entity_type, entity_id);

-- Product Categories
CREATE INDEX idx_product_categories_tenant ON product_categories(tenant_id);
CREATE INDEX idx_product_categories_parent ON product_categories(parent_id);

-- Products
CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);
CREATE INDEX idx_barcodes_product ON barcodes(product_id);
CREATE INDEX idx_product_units_product ON product_units(product_id);
CREATE INDEX idx_price_history_product ON product_price_history(product_id);
CREATE INDEX idx_customer_prices_customer ON customer_price_lists(customer_id);
CREATE INDEX idx_customer_prices_product ON customer_price_lists(product_id);
CREATE INDEX idx_supplier_products_supplier ON supplier_products(supplier_id);
CREATE INDEX idx_supplier_products_product ON supplier_products(product_id);

-- Inventory
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_movements_tenant ON inventory_movements(tenant_id);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_inventory_batches_product ON inventory_batches(product_id);
CREATE INDEX idx_inventory_batches_expiry ON inventory_batches(expiry_date);
CREATE INDEX idx_stock_transfers_tenant ON stock_transfers(tenant_id);

-- Orders & Quotations
CREATE INDEX idx_quotations_tenant ON quotations(tenant_id);
CREATE INDEX idx_quotations_customer ON quotations(customer_id);
CREATE INDEX idx_sales_orders_tenant ON sales_orders(tenant_id);
CREATE INDEX idx_sales_orders_customer ON sales_orders(customer_id);
CREATE INDEX idx_purchase_orders_tenant ON purchase_orders(tenant_id);
CREATE INDEX idx_purchase_orders_supplier ON purchase_orders(supplier_id);

-- Sales
CREATE INDEX idx_sales_invoices_tenant ON sales_invoices(tenant_id);
CREATE INDEX idx_sales_invoices_company ON sales_invoices(company_id);
CREATE INDEX idx_sales_invoices_customer ON sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_branch ON sales_invoices(branch_id);
CREATE INDEX idx_sales_invoices_status ON sales_invoices(status);
CREATE INDEX idx_sales_invoices_date ON sales_invoices(created_at);
CREATE INDEX idx_sales_invoices_due_date ON sales_invoices(due_date);
CREATE INDEX idx_sales_items_invoice ON sales_items(invoice_id);
CREATE INDEX idx_sales_items_product ON sales_items(product_id);

-- Purchases
CREATE INDEX idx_purchase_invoices_tenant ON purchase_invoices(tenant_id);
CREATE INDEX idx_purchase_invoices_company ON purchase_invoices(company_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_branch ON purchase_invoices(branch_id);
CREATE INDEX idx_purchase_items_invoice ON purchase_items(invoice_id);

-- Credit & Debit Notes
CREATE INDEX idx_credit_notes_tenant ON credit_notes(tenant_id);
CREATE INDEX idx_credit_notes_customer ON credit_notes(customer_id);
CREATE INDEX idx_credit_note_items_note ON credit_note_items(credit_note_id);
CREATE INDEX idx_debit_notes_tenant ON debit_notes(tenant_id);
CREATE INDEX idx_debit_notes_supplier ON debit_notes(supplier_id);

-- Payments & Treasury
CREATE INDEX idx_payments_tenant ON payments(tenant_id);
CREATE INDEX idx_payments_company ON payments(company_id);
CREATE INDEX idx_payments_treasury ON payments(treasury_id);
CREATE INDEX idx_cheques_payment ON cheques(payment_id);
CREATE INDEX idx_cheques_status ON cheques(status);
CREATE INDEX idx_expenses_tenant ON expenses(tenant_id);
CREATE INDEX idx_expenses_company ON expenses(company_id);

-- Accounting
CREATE INDEX idx_accounts_tenant ON accounts(tenant_id);
CREATE INDEX idx_accounts_company ON accounts(company_id);
CREATE INDEX idx_accounts_parent ON accounts(parent_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_journal_entry_lines_entry ON journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON journal_entry_lines(account_id);
CREATE INDEX idx_ledger_snapshots_account ON ledger_snapshots(account_id);

-- AI
CREATE INDEX idx_ai_conversations_user ON ai_conversations(user_id);
CREATE INDEX idx_ai_feedback_log ON ai_feedback(ai_log_id);

-- Notifications
CREATE INDEX idx_notifications_tenant ON notifications(tenant_id);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);
CREATE INDEX idx_realtime_notifications_user ON realtime_notifications(user_id);

-- Attachments
CREATE INDEX idx_attachments_entity ON attachments(entity_type, entity_id);

-- Background Jobs
CREATE INDEX idx_background_jobs_status ON background_jobs(status);

-- Rate Limits
CREATE INDEX idx_api_rate_limits_user ON api_rate_limits(user_id);
CREATE INDEX idx_api_rate_limits_tenant ON api_rate_limits(tenant_id);

-- Warehouses
CREATE INDEX idx_warehouses_tenant ON warehouses(tenant_id);
CREATE INDEX idx_warehouses_company ON warehouses(company_id);
CREATE INDEX idx_warehouses_branch ON warehouses(branch_id);

-- Webhooks
CREATE INDEX idx_webhooks_tenant ON webhooks(tenant_id);
CREATE INDEX idx_webhooks_event ON webhooks(event_type);
CREATE INDEX idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);

-- Subscriptions
CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Manufacturing
CREATE INDEX idx_bom_product ON bill_of_materials(product_id);
CREATE INDEX idx_bom_material ON bill_of_materials(material_id);
CREATE INDEX idx_production_orders_tenant ON production_orders(tenant_id);
CREATE INDEX idx_production_orders_status ON production_orders(status);

-- HR
CREATE INDEX idx_employees_tenant ON employees(tenant_id);
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_attendance_employee ON attendance(employee_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_payroll_employee ON payroll(employee_id);

-- POS
CREATE INDEX idx_pos_sessions_tenant ON pos_sessions(tenant_id);
CREATE INDEX idx_pos_sessions_branch ON pos_sessions(branch_id);

-- Health
CREATE INDEX idx_system_health_type ON system_health_metrics(metric_type);
CREATE INDEX idx_system_health_date ON system_health_metrics(created_at);

-- ============================================================
-- COMPOSITE INDEXES (Common Query Patterns)
-- ============================================================

CREATE INDEX idx_sales_invoices_company_date ON sales_invoices(company_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_purchase_invoices_company_date ON purchase_invoices(company_id, created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_inventory_low_stock ON inventory(product_id, quantity) WHERE quantity < 10;
CREATE INDEX idx_cheques_due ON cheques(due_date) WHERE status = 'pending';

-- ============================================================
-- PARTIAL INDEXES (Soft Delete Performance)
-- ============================================================

CREATE INDEX idx_active_products ON products(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_customers ON customers(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_suppliers ON suppliers(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_warehouses ON warehouses(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_sales_invoices ON sales_invoices(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_purchase_invoices ON purchase_invoices(id) WHERE deleted_at IS NULL;
CREATE INDEX idx_active_accounts ON accounts(id) WHERE deleted_at IS NULL;

-- ============================================================
-- VECTOR INDEX (HNSW for production - better recall than ivfflat)
-- ============================================================

-- Note: Create AFTER inserting initial data for best performance
-- CREATE INDEX idx_ai_embedding ON ai_logs USING hnsw (embedding vector_cosine_ops);

-- ============================================================
-- MATERIALIZED VIEWS (Analytics)
-- ============================================================

CREATE MATERIALIZED VIEW monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    tenant_id,
    company_id,
    branch_id,
    COUNT(*) AS invoice_count,
    SUM(total) AS total_sales,
    SUM(discount) AS total_discounts,
    SUM(amount_paid) AS total_collected
FROM sales_invoices
WHERE deleted_at IS NULL
GROUP BY month, tenant_id, company_id, branch_id;

CREATE MATERIALIZED VIEW monthly_purchase_summary AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    tenant_id,
    company_id,
    branch_id,
    COUNT(*) AS invoice_count,
    SUM(total) AS total_purchases,
    SUM(amount_paid) AS total_paid
FROM purchase_invoices
WHERE deleted_at IS NULL
GROUP BY month, tenant_id, company_id, branch_id;

CREATE MATERIALIZED VIEW product_profit_summary AS
SELECT
    si.product_id,
    p.name AS product_name,
    p.tenant_id,
    SUM(si.quantity) AS total_sold,
    SUM(si.gross_profit) AS total_gross_profit,
    SUM(si.net_profit) AS total_net_profit
FROM sales_items si
JOIN products p ON p.id = si.product_id
GROUP BY si.product_id, p.name, p.tenant_id;

-- Computed treasury balance (replaces stored balance column)
CREATE MATERIALIZED VIEW treasury_balances AS
SELECT
    t.id AS treasury_id,
    t.tenant_id,
    t.name,
    t.currency_id,
    COALESCE(SUM(p.amount), 0) - COALESCE(SUM(e.amount), 0) AS computed_balance
FROM treasury t
LEFT JOIN payments p ON p.treasury_id = t.id
LEFT JOIN expenses e ON e.treasury_id = t.id
GROUP BY t.id, t.tenant_id, t.name, t.currency_id;

-- Computed account balance (replaces stored balance column)
CREATE MATERIALIZED VIEW account_balances AS
SELECT
    a.id AS account_id,
    a.tenant_id,
    a.account_code,
    a.account_name,
    a.account_type,
    COALESCE(SUM(jel.debit), 0) - COALESCE(SUM(jel.credit), 0) AS computed_balance
FROM accounts a
LEFT JOIN journal_entry_lines jel ON jel.account_id = a.id
GROUP BY a.id, a.tenant_id, a.account_code, a.account_name, a.account_type;

-- ============================================================
-- DEFERRED FOREIGN KEYS (created_by, updated_by, deleted_by)
-- Added via ALTER TABLE to resolve circular dependencies
-- ============================================================

-- Companies
ALTER TABLE companies ADD CONSTRAINT fk_companies_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE companies ADD CONSTRAINT fk_companies_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE companies ADD CONSTRAINT fk_companies_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Branches
ALTER TABLE branches ADD CONSTRAINT fk_branches_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE branches ADD CONSTRAINT fk_branches_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE branches ADD CONSTRAINT fk_branches_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Users (self-reference)
ALTER TABLE users ADD CONSTRAINT fk_users_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Customers
ALTER TABLE customers ADD CONSTRAINT fk_customers_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE customers ADD CONSTRAINT fk_customers_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE customers ADD CONSTRAINT fk_customers_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Suppliers
ALTER TABLE suppliers ADD CONSTRAINT fk_suppliers_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE suppliers ADD CONSTRAINT fk_suppliers_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE suppliers ADD CONSTRAINT fk_suppliers_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Products
ALTER TABLE products ADD CONSTRAINT fk_products_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE products ADD CONSTRAINT fk_products_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE products ADD CONSTRAINT fk_products_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Warehouses
ALTER TABLE warehouses ADD CONSTRAINT fk_warehouses_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE warehouses ADD CONSTRAINT fk_warehouses_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE warehouses ADD CONSTRAINT fk_warehouses_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Sales Invoices
ALTER TABLE sales_invoices ADD CONSTRAINT fk_sales_invoices_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sales_invoices ADD CONSTRAINT fk_sales_invoices_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE sales_invoices ADD CONSTRAINT fk_sales_invoices_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Purchase Invoices
ALTER TABLE purchase_invoices ADD CONSTRAINT fk_purchase_invoices_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE purchase_invoices ADD CONSTRAINT fk_purchase_invoices_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE purchase_invoices ADD CONSTRAINT fk_purchase_invoices_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Accounts
ALTER TABLE accounts ADD CONSTRAINT fk_accounts_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE accounts ADD CONSTRAINT fk_accounts_updated_by FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE accounts ADD CONSTRAINT fk_accounts_deleted_by FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;

-- Quotations
ALTER TABLE quotations ADD CONSTRAINT fk_quotations_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Sales Orders
ALTER TABLE sales_orders ADD CONSTRAINT fk_sales_orders_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Purchase Orders
ALTER TABLE purchase_orders ADD CONSTRAINT fk_purchase_orders_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Credit Notes
ALTER TABLE credit_notes ADD CONSTRAINT fk_credit_notes_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Debit Notes
ALTER TABLE debit_notes ADD CONSTRAINT fk_debit_notes_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Production Orders
ALTER TABLE production_orders ADD CONSTRAINT fk_production_orders_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Exchange Rates
ALTER TABLE exchange_rates ADD CONSTRAINT fk_exchange_rates_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;

-- Journal Entries (partition-safe: no FK to partitioned table, but FK from it)
ALTER TABLE journal_entries ADD CONSTRAINT fk_journal_entries_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE journal_entries ADD CONSTRAINT fk_journal_entries_fiscal_year FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id) ON DELETE SET NULL;
ALTER TABLE journal_entries ADD CONSTRAINT fk_journal_entries_cost_center FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id) ON DELETE SET NULL;

-- Background Jobs
ALTER TABLE background_jobs ADD CONSTRAINT fk_background_jobs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- Outbox Events
ALTER TABLE outbox_events ADD CONSTRAINT fk_outbox_events_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default Units
INSERT INTO units (name, symbol) VALUES
    ('piece', 'pc'),
    ('kilogram', 'kg'),
    ('gram', 'g'),
    ('liter', 'L'),
    ('meter', 'm'),
    ('box', 'box'),
    ('carton', 'ctn'),
    ('dozen', 'dz'),
    ('pack', 'pk'),
    ('ton', 't');

-- Default Currencies
INSERT INTO currencies (code, name, symbol) VALUES
    ('EGP', 'Egyptian Pound', 'E£'),
    ('USD', 'US Dollar', '$'),
    ('EUR', 'Euro', '€'),
    ('SAR', 'Saudi Riyal', '﷼'),
    ('AED', 'UAE Dirham', 'د.إ'),
    ('GBP', 'British Pound', '£');

-- Default Languages
INSERT INTO languages (code, name, is_rtl) VALUES
    ('ar', 'Arabic', TRUE),
    ('en', 'English', FALSE),
    ('fr', 'French', FALSE);

-- Default Permissions (Module.Action.Scope)
INSERT INTO permissions (name, module, action, scope, description) VALUES
    ('sales.invoice.create', 'sales', 'create', 'own', 'Create sales invoices'),
    ('sales.invoice.read', 'sales', 'read', 'all', 'View sales invoices'),
    ('sales.invoice.update', 'sales', 'update', 'own', 'Update sales invoices'),
    ('sales.invoice.delete', 'sales', 'delete', 'own', 'Delete sales invoices'),
    ('sales.invoice.approve', 'sales', 'approve', 'all', 'Approve sales invoices'),
    ('inventory.stock.read', 'inventory', 'read', 'all', 'View inventory'),
    ('inventory.stock.manage', 'inventory', 'manage', 'all', 'Manage stock movements'),
    ('finance.treasury.read', 'finance', 'read', 'all', 'View treasury'),
    ('finance.treasury.manage', 'finance', 'manage', 'all', 'Manage treasury'),
    ('finance.journal.create', 'finance', 'create', 'all', 'Create journal entries'),
    ('finance.journal.approve', 'finance', 'approve', 'all', 'Approve journal entries'),
    ('reports.view', 'reports', 'read', 'all', 'View reports'),
    ('admin.users.manage', 'admin', 'manage', 'all', 'Manage users'),
    ('admin.settings.manage', 'admin', 'manage', 'all', 'Manage settings'),
    ('admin.branches.manage', 'admin', 'manage', 'all', 'Manage branches'),
    ('hr.employees.manage', 'hr', 'manage', 'all', 'Manage employees'),
    ('hr.payroll.manage', 'hr', 'manage', 'all', 'Manage payroll'),
    ('manufacturing.orders.manage', 'manufacturing', 'manage', 'all', 'Manage production'),
    ('ai.query', 'ai', 'query', 'all', 'Use AI features'),
    ('pos.session.manage', 'pos', 'manage', 'own', 'Manage POS sessions');

-- Default Taxes
INSERT INTO taxes (name, percentage, tax_type, is_inclusive, is_active) VALUES
    ('VAT 14%', 14.00, 'vat', FALSE, TRUE),
    ('VAT 5%', 5.00, 'vat', FALSE, TRUE),
    ('No Tax', 0.00, 'exempt', FALSE, TRUE);

-- Default Feature Flags
INSERT INTO feature_flags (name, enabled) VALUES
    ('ai_module', TRUE),
    ('manufacturing_module', FALSE),
    ('multi_currency', TRUE),
    ('webhook_system', FALSE),
    ('pos_module', FALSE),
    ('hr_module', FALSE),
    ('crm_pipeline', TRUE),
    ('e_invoice', FALSE);

-- Schema version
INSERT INTO schema_migrations (version, name) VALUES
    ('v5.0.0', 'Enterprise SaaS - fixed integrity issues, added missing tables'),
    ('v5.1.0', 'Added missing foreign keys for created_by, updated_by, deleted_by and other loose references'),
    ('v6.0.0', 'Comprehensive fix: removed denormalized balances, added credit_note_items, debit_notes, product_categories, webhook_deliveries, scheduled_report_recipients, price history trigger, RLS policies, NUMERIC quantities, approval thresholds, leave approvals, production timing');
