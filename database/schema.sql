-- Ceramix AI ERP - Database Schema (v3 - Enterprise)
-- PostgreSQL Database
-- UUID-based, normalized, transaction-safe, multi-tenant architecture
-- Multi-company, multi-branch, multi-currency, double-entry accounting, AI-ready

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- 1. MULTI-COMPANY & MULTI-BRANCH MODULE
-- ============================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- ============================================================
-- 2. MULTI-CURRENCY SYSTEM
-- ============================================================

CREATE TABLE currencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50),
    symbol VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    rate NUMERIC(18, 6) NOT NULL,
    rate_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. AUTHENTICATION MODULE
-- ============================================================

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- ============================================================
-- 4. SESSION & SECURITY TRACKING
-- ============================================================

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    api_key TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. CRM MODULE (with Soft Delete & Multi-Tenant)
-- ============================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    credit_limit NUMERIC(12, 2) DEFAULT 0,
    balance NUMERIC(12, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    phone VARCHAR(30),
    balance NUMERIC(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- 6. TAX ENGINE
-- ============================================================

CREATE TABLE taxes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    percentage NUMERIC(5, 2) NOT NULL,
    tax_type VARCHAR(30),
    is_inclusive BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 7. PRODUCTS MODULE (with Soft Delete, Full Text Search & Multi-Tenant)
-- ============================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE,
    category VARCHAR(100),
    unit VARCHAR(30) DEFAULT 'piece',
    sale_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    purchase_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    average_cost NUMERIC(12, 2) DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    tax_id UUID REFERENCES taxes(id) ON DELETE SET NULL,
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- 8. PRODUCT UNITS & CONVERSION SYSTEM
-- ============================================================

CREATE TABLE product_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    unit_name VARCHAR(50) NOT NULL,
    conversion_factor NUMERIC(12, 4) NOT NULL DEFAULT 1,
    is_default BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- 9. BARCODE / POS SUPPORT
-- ============================================================

CREATE TABLE barcodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    barcode VARCHAR(100) UNIQUE NOT NULL
);

-- ============================================================
-- 10. WAREHOUSE MODULE (with Branch & Multi-Tenant)
-- ============================================================

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================
-- 11. ADVANCED INVENTORY SYSTEM
-- ============================================================

CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    in_transit_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, warehouse_id),
    CONSTRAINT chk_inventory_quantity CHECK (quantity >= 0)
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    from_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    to_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    reason VARCHAR(50) NOT NULL CHECK (reason IN ('purchase', 'sale', 'transfer', 'return', 'adjustment', 'production')),
    reference_id UUID,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 12. INVENTORY BATCH / LOT TRACKING
-- ============================================================

CREATE TABLE inventory_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE,
    batch_number VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100),
    quantity INTEGER NOT NULL,
    manufacturing_date DATE,
    expiry_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 13. SALES MODULE (with Branch, Tax, Profit & Multi-Currency)
-- ============================================================

CREATE TABLE sales_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    payment_type VARCHAR(30) DEFAULT 'cash',
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'posted', 'paid', 'partial', 'cancelled', 'reversed', 'archived')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE sales_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES sales_invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    tax_id UUID REFERENCES taxes(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) DEFAULT 0,
    tax_percent NUMERIC(5, 2) DEFAULT 0,
    tax_amount NUMERIC(12, 2) DEFAULT 0,
    average_cost NUMERIC(12, 2) DEFAULT 0,
    gross_profit NUMERIC(12, 2) DEFAULT 0,
    net_profit NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL
);

-- ============================================================
-- 14. PURCHASE MODULE (with Branch, Tax & Multi-Currency)
-- ============================================================

CREATE TABLE purchase_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'posted', 'paid', 'partial', 'cancelled', 'reversed', 'archived')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE purchase_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    tax_id UUID REFERENCES taxes(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_percent NUMERIC(5, 2) DEFAULT 0,
    tax_amount NUMERIC(12, 2) DEFAULT 0
);

-- ============================================================
-- 15. TREASURY & FINANCE MODULE (with Multi-Currency)
-- ============================================================

CREATE TABLE treasury (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    balance NUMERIC(14, 2) DEFAULT 0,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    sales_invoice_id UUID REFERENCES sales_invoices(id) ON DELETE SET NULL,
    purchase_invoice_id UUID REFERENCES purchase_invoices(id) ON DELETE SET NULL,
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    amount NUMERIC(12, 2) NOT NULL,
    method VARCHAR(30) NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'cheque')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_payment_amount CHECK (amount > 0)
);

CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 16. DOUBLE ENTRY ACCOUNTING SYSTEM
-- ============================================================

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    account_code VARCHAR(50) UNIQUE NOT NULL,
    account_name VARCHAR(150) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    balance NUMERIC(14, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_type VARCHAR(50),
    reference_id UUID,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    journal_entry_id UUID NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    debit NUMERIC(14, 2) DEFAULT 0,
    credit NUMERIC(14, 2) DEFAULT 0,
    CONSTRAINT chk_debit_credit CHECK (
        (debit > 0 AND credit = 0)
        OR (credit > 0 AND debit = 0)
    )
);

-- ============================================================
-- 17. RETURNS MODULE
-- ============================================================

CREATE TABLE returns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    return_type VARCHAR(30) NOT NULL CHECK (return_type IN ('sales_return', 'purchase_return')),
    sales_invoice_id UUID REFERENCES sales_invoices(id) ON DELETE SET NULL,
    purchase_invoice_id UUID REFERENCES purchase_invoices(id) ON DELETE SET NULL,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    refund_amount NUMERIC(12, 2) DEFAULT 0,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 18. AI & ANALYTICS MODULE (Enhanced with Embeddings)
-- ============================================================

CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    conversation_id UUID REFERENCES ai_conversations(id) ON DELETE SET NULL,
    user_query TEXT,
    generated_sql TEXT,
    ai_response TEXT,
    detected_intent VARCHAR(100),
    confidence_score NUMERIC(5, 2),
    execution_time_ms INTEGER,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE analytics_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_type VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 19. AUDIT & MONITORING MODULE (Enhanced + Partitioned)
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    table_name VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    ip_address VARCHAR(45),
    endpoint TEXT,
    method VARCHAR(10),
    device_info TEXT,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- ============================================================
-- 20. NOTIFICATION SYSTEM (with Multi-Tenant)
-- ============================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 21. APPROVAL WORKFLOW SYSTEM
-- ============================================================

CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE approval_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES approval_workflows(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL
);

-- ============================================================
-- 22. REALTIME & EVENT ARCHITECTURE (Partitioned)
-- ============================================================

CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- ============================================================
-- 23. FILE MANAGEMENT SYSTEM
-- ============================================================

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50),
    entity_id UUID,
    file_name VARCHAR(255),
    file_url TEXT,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 24. SETTINGS SYSTEM
-- ============================================================

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 25. MANUFACTURING MODULE
-- ============================================================

CREATE TABLE bill_of_materials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    material_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE production_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity NUMERIC(12, 2) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 26. SAAS SUBSCRIPTION SYSTEM
-- ============================================================

CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    max_users INTEGER,
    max_branches INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'trial')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 27. FEATURE FLAGS SYSTEM
-- ============================================================

CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 28. WEBHOOK SYSTEM
-- ============================================================

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    target_url TEXT NOT NULL,
    secret_key TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 29. SCHEDULED REPORTS SYSTEM
-- ============================================================

CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_name VARCHAR(255) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 30. BACKGROUND JOBS / QUEUE SYSTEM
-- ============================================================

CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(100) NOT NULL,
    payload JSONB,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- ============================================================
-- 31. API RATE LIMITING
-- ============================================================

CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES (Performance Optimization)
-- ============================================================

-- Companies & Branches
CREATE INDEX idx_branches_company ON branches(company_id);

-- Currency
CREATE INDEX idx_exchange_rates_pair ON exchange_rates(from_currency, to_currency);
CREATE INDEX idx_exchange_rates_date ON exchange_rates(rate_date);

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_branch ON users(branch_id);

-- Sessions & API Keys
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- Customers & Suppliers
CREATE INDEX idx_customers_company ON customers(company_id);
CREATE INDEX idx_customers_name ON customers(full_name);
CREATE INDEX idx_customers_deleted ON customers(deleted_at);
CREATE INDEX idx_suppliers_company ON suppliers(company_id);
CREATE INDEX idx_suppliers_name ON suppliers(company_name);
CREATE INDEX idx_suppliers_deleted ON suppliers(deleted_at);

-- Products
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_deleted ON products(deleted_at);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);

-- Barcodes
CREATE INDEX idx_barcodes_product ON barcodes(product_id);

-- Product Units
CREATE INDEX idx_product_units_product ON product_units(product_id);

-- Inventory
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_inventory_movements_reason ON inventory_movements(reason);
CREATE INDEX idx_inventory_batches_product ON inventory_batches(product_id);
CREATE INDEX idx_inventory_batches_expiry ON inventory_batches(expiry_date);

-- Sales
CREATE INDEX idx_sales_invoices_company ON sales_invoices(company_id);
CREATE INDEX idx_sales_invoices_customer ON sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_branch ON sales_invoices(branch_id);
CREATE INDEX idx_sales_invoices_status ON sales_invoices(status);
CREATE INDEX idx_sales_invoices_date ON sales_invoices(created_at);
CREATE INDEX idx_sales_items_invoice ON sales_items(invoice_id);
CREATE INDEX idx_sales_items_product ON sales_items(product_id);

-- Purchases
CREATE INDEX idx_purchase_invoices_company ON purchase_invoices(company_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_branch ON purchase_invoices(branch_id);
CREATE INDEX idx_purchase_items_invoice ON purchase_items(invoice_id);

-- Payments
CREATE INDEX idx_payments_company ON payments(company_id);
CREATE INDEX idx_payments_treasury ON payments(treasury_id);
CREATE INDEX idx_payments_sales ON payments(sales_invoice_id);
CREATE INDEX idx_payments_purchases ON payments(purchase_invoice_id);

-- Accounting
CREATE INDEX idx_accounts_company ON accounts(company_id);
CREATE INDEX idx_accounts_parent ON accounts(parent_id);
CREATE INDEX idx_accounts_type ON accounts(account_type);
CREATE INDEX idx_journal_entry_lines_entry ON journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_entry_lines_account ON journal_entry_lines(account_id);

-- AI
CREATE INDEX idx_ai_conversations_user ON ai_conversations(user_id);

-- Notifications
CREATE INDEX idx_notifications_company ON notifications(company_id);
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_read ON notifications(is_read);

-- Attachments
CREATE INDEX idx_attachments_entity ON attachments(entity_type, entity_id);

-- Background Jobs
CREATE INDEX idx_background_jobs_status ON background_jobs(status);

-- Rate Limits
CREATE INDEX idx_api_rate_limits_user ON api_rate_limits(user_id);

-- Warehouses
CREATE INDEX idx_warehouses_company ON warehouses(company_id);
CREATE INDEX idx_warehouses_branch ON warehouses(branch_id);

-- Webhooks
CREATE INDEX idx_webhooks_company ON webhooks(company_id);
CREATE INDEX idx_webhooks_event ON webhooks(event_type);

-- Subscriptions
CREATE INDEX idx_subscriptions_company ON subscriptions(company_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Manufacturing
CREATE INDEX idx_bom_product ON bill_of_materials(product_id);
CREATE INDEX idx_bom_material ON bill_of_materials(material_id);
CREATE INDEX idx_production_orders_product ON production_orders(product_id);
CREATE INDEX idx_production_orders_status ON production_orders(status);

-- ============================================================
-- MATERIALIZED VIEWS (Analytics)
-- ============================================================

CREATE MATERIALIZED VIEW monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    company_id,
    branch_id,
    COUNT(*) AS invoice_count,
    SUM(total) AS total_sales,
    SUM(discount) AS total_discounts,
    SUM(amount_paid) AS total_collected
FROM sales_invoices
WHERE deleted_at IS NULL
GROUP BY month, company_id, branch_id;

CREATE MATERIALIZED VIEW monthly_purchase_summary AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    company_id,
    branch_id,
    COUNT(*) AS invoice_count,
    SUM(total) AS total_purchases,
    SUM(amount_paid) AS total_paid
FROM purchase_invoices
WHERE deleted_at IS NULL
GROUP BY month, company_id, branch_id;

CREATE MATERIALIZED VIEW product_profit_summary AS
SELECT
    si.product_id,
    p.name AS product_name,
    SUM(si.quantity) AS total_sold,
    SUM(si.gross_profit) AS total_gross_profit,
    SUM(si.net_profit) AS total_net_profit
FROM sales_items si
JOIN products p ON p.id = si.product_id
GROUP BY si.product_id, p.name;

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default Currencies
INSERT INTO currencies (code, name, symbol) VALUES
    ('EGP', 'Egyptian Pound', 'E£'),
    ('USD', 'US Dollar', '$'),
    ('EUR', 'Euro', '€'),
    ('SAR', 'Saudi Riyal', '﷼');

-- Default Roles
INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('accountant', 'Financial operations and reporting'),
    ('sales', 'Sales and customer management'),
    ('warehouse', 'Inventory and stock management'),
    ('manufacturing', 'Production and BOM management');

-- Default Permissions
INSERT INTO permissions (name, description) VALUES
    ('create_invoice', 'Create sales/purchase invoices'),
    ('manage_inventory', 'Manage stock and warehouses'),
    ('view_reports', 'View financial and analytics reports'),
    ('manage_users', 'Create and manage system users'),
    ('manage_treasury', 'Manage treasury and payments'),
    ('manage_returns', 'Process sales and purchase returns'),
    ('view_audit_logs', 'View system audit logs'),
    ('ai_query', 'Use AI query features'),
    ('manage_branches', 'Manage companies and branches'),
    ('approve_workflows', 'Approve workflow steps'),
    ('manage_settings', 'Manage system settings'),
    ('manage_manufacturing', 'Manage production orders and BOM'),
    ('manage_subscriptions', 'Manage SaaS subscriptions');

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
    ('pos_module', FALSE);
