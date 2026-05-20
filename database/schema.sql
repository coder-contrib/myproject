-- Ceramix AI ERP - Database Schema (v4 - Enterprise SaaS)
-- PostgreSQL 14+
-- Multi-tenant, UUID-based, RLS-enabled, event-sourced, AI-powered
-- Full ERP + CRM + HR + Manufacturing + POS + Double-Entry Accounting

-- ============================================================
-- EXTENSIONS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- AUTOMATIC updated_at TRIGGER FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- ============================================================
-- 1. TENANT SYSTEM (True SaaS Isolation)
-- ============================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subscription_status VARCHAR(50) DEFAULT 'trial',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 2. MULTI-COMPANY & MULTI-BRANCH
-- ============================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    inventory_valuation_method VARCHAR(30) DEFAULT 'weighted_average' CHECK (inventory_valuation_method IN ('fifo', 'lifo', 'weighted_average')),
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    address TEXT,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- ============================================================
-- 3. MULTI-CURRENCY SYSTEM
-- ============================================================

CREATE TABLE currencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50),
    symbol VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_currency VARCHAR(10) NOT NULL,
    to_currency VARCHAR(10) NOT NULL,
    rate NUMERIC(18, 6) NOT NULL,
    rate_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. AUTHENTICATION MODULE
-- ============================================================

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL UNIQUE,
    module VARCHAR(50),
    action VARCHAR(50),
    scope VARCHAR(50),
    description TEXT
);

CREATE TABLE role_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- ============================================================
-- 5. SESSION & SECURITY
-- ============================================================

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    api_key_hash TEXT NOT NULL,
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 6. LOCALIZATION / i18n
-- ============================================================

CREATE TABLE languages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    is_rtl BOOLEAN DEFAULT FALSE
);

CREATE TABLE translations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language_id UUID REFERENCES languages(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    UNIQUE(language_id, key)
);

-- ============================================================
-- 7. CRM MODULE (with Soft Delete & Multi-Tenant)
-- ============================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    credit_limit NUMERIC(12, 2) DEFAULT 0,
    balance NUMERIC(12, 2) DEFAULT 0,
    notes TEXT,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    company_name VARCHAR(200) NOT NULL,
    phone VARCHAR(30),
    balance NUMERIC(12, 2) DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- ============================================================
-- 8. CRM PIPELINE (Leads, Opportunities, Activities)
-- ============================================================

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    source VARCHAR(50),
    status VARCHAR(30) DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'lost')),
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    expected_value NUMERIC(14, 2),
    stage VARCHAR(50) DEFAULT 'prospecting',
    probability NUMERIC(5, 2) DEFAULT 0,
    close_date DATE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_id UUID,
    activity_type VARCHAR(50),
    description TEXT,
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 9. TAX ENGINE
-- ============================================================

CREATE TABLE taxes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    percentage NUMERIC(5, 2) NOT NULL,
    tax_type VARCHAR(30),
    is_inclusive BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 10. PRODUCTS MODULE
-- ============================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50),
    category VARCHAR(100),
    unit VARCHAR(30) DEFAULT 'piece',
    sale_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    purchase_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    average_cost NUMERIC(12, 2) DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    tax_id UUID REFERENCES taxes(id) ON DELETE SET NULL,
    search_vector tsvector,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID,
    UNIQUE(tenant_id, sku)
);

CREATE TABLE product_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    unit_name VARCHAR(50) NOT NULL,
    conversion_factor NUMERIC(12, 4) NOT NULL DEFAULT 1,
    is_default BOOLEAN DEFAULT FALSE
);

CREATE TABLE barcodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    barcode VARCHAR(100) UNIQUE NOT NULL
);

-- ============================================================
-- 11. WAREHOUSE MODULE
-- ============================================================

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    location TEXT,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID
);

-- ============================================================
-- 12. ADVANCED INVENTORY SYSTEM
-- ============================================================

CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    from_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    to_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    reason VARCHAR(50) NOT NULL CHECK (reason IN ('purchase', 'sale', 'transfer', 'return', 'adjustment', 'production')),
    reference_id UUID,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inventory_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
-- 13. DOCUMENT SEQUENCES (Invoice Numbering)
-- ============================================================

CREATE TABLE document_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    document_type VARCHAR(50) NOT NULL,
    prefix VARCHAR(20),
    next_number INTEGER DEFAULT 1,
    fiscal_year VARCHAR(10),
    UNIQUE(tenant_id, company_id, branch_id, document_type, fiscal_year)
);

-- ============================================================
-- 14. QUOTATIONS & ORDERS
-- ============================================================

CREATE TABLE quotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    quotation_number VARCHAR(50) NOT NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    subtotal NUMERIC(12, 2) DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) DEFAULT 0,
    valid_until DATE,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'expired', 'converted')),
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE quotation_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quotation_id UUID NOT NULL REFERENCES quotations(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL
);

CREATE TABLE sales_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    order_number VARCHAR(50) NOT NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    subtotal NUMERIC(12, 2) DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sales_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES sales_orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL
);

CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    order_number VARCHAR(50) NOT NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    total NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'confirmed', 'received', 'cancelled')),
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);

-- ============================================================
-- 15. SALES MODULE
-- ============================================================

CREATE TABLE sales_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    sales_order_id UUID REFERENCES sales_orders(id) ON DELETE SET NULL,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    payment_type VARCHAR(30) DEFAULT 'cash',
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'posted', 'paid', 'partial', 'cancelled', 'reversed', 'archived')),
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID,
    UNIQUE(tenant_id, invoice_number)
);

CREATE TABLE sales_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
-- 16. PURCHASE MODULE
-- ============================================================

CREATE TABLE purchase_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    purchase_order_id UUID REFERENCES purchase_orders(id) ON DELETE SET NULL,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'posted', 'paid', 'partial', 'cancelled', 'reversed', 'archived')),
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID,
    UNIQUE(tenant_id, invoice_number)
);

CREATE TABLE purchase_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    tax_id UUID REFERENCES taxes(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    tax_percent NUMERIC(5, 2) DEFAULT 0,
    tax_amount NUMERIC(12, 2) DEFAULT 0
);

-- ============================================================
-- 17. TREASURY & FINANCE (Multi-Currency)
-- ============================================================

CREATE TABLE treasury (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    balance NUMERIC(14, 2) DEFAULT 0,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    sales_invoice_id UUID REFERENCES sales_invoices(id) ON DELETE SET NULL,
    purchase_invoice_id UUID REFERENCES purchase_invoices(id) ON DELETE SET NULL,
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    amount NUMERIC(12, 2) NOT NULL,
    method VARCHAR(30) NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'cheque', 'credit_card', 'mobile_payment')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_payment_amount CHECK (amount > 0)
);

CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    currency_id UUID REFERENCES currencies(id) ON DELETE SET NULL,
    cost_center_id UUID,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 18. FISCAL YEAR SYSTEM
-- ============================================================

CREATE TABLE fiscal_years (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    year_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 19. COST CENTERS
-- ============================================================

CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL
);

ALTER TABLE expenses
ADD CONSTRAINT fk_expenses_cost_center
FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id) ON DELETE SET NULL;

-- ============================================================
-- 20. DOUBLE ENTRY ACCOUNTING
-- ============================================================

CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(150) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    balance NUMERIC(14, 2) DEFAULT 0,
    version INTEGER DEFAULT 1,
    created_by UUID,
    updated_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    deleted_by UUID,
    UNIQUE(tenant_id, account_code)
);

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    fiscal_year_id UUID REFERENCES fiscal_years(id) ON DELETE SET NULL,
    cost_center_id UUID REFERENCES cost_centers(id) ON DELETE SET NULL,
    reference_type VARCHAR(50),
    reference_id UUID,
    description TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    debit NUMERIC(14, 2) DEFAULT 0,
    credit NUMERIC(14, 2) DEFAULT 0,
    CONSTRAINT chk_debit_credit CHECK (
        (debit > 0 AND credit = 0)
        OR (credit > 0 AND debit = 0)
    ),
    CONSTRAINT chk_non_negative CHECK (debit >= 0 AND credit >= 0)
);

CREATE TABLE ledger_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    fiscal_year_id UUID REFERENCES fiscal_years(id) ON DELETE CASCADE,
    period_end DATE NOT NULL,
    balance NUMERIC(14, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 21. RETURNS MODULE
-- ============================================================

CREATE TABLE returns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
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
-- 22. E-INVOICE / TAX AUTHORITY
-- ============================================================

CREATE TABLE tax_authority_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    invoice_id UUID,
    invoice_type VARCHAR(30),
    submission_id VARCHAR(255),
    status VARCHAR(50),
    response_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 23. AI MODULE (Enhanced with Embeddings & Training)
-- ============================================================

CREATE TABLE ai_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

CREATE TABLE ai_training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    input_text TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE ai_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ai_log_id UUID,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    template TEXT NOT NULL,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 24. AUDIT & MONITORING (Partitioned)
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
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

CREATE TABLE api_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    user_id UUID,
    endpoint TEXT NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_body JSONB,
    response_code INTEGER,
    latency_ms INTEGER,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- ============================================================
-- 25. NOTIFICATION SYSTEM
-- ============================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE realtime_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    delivered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 26. APPROVAL WORKFLOW SYSTEM
-- ============================================================

CREATE TABLE approval_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE approval_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES approval_workflows(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL
);

-- ============================================================
-- 27. EVENT SYSTEM (Event Sourcing + Outbox)
-- ============================================================

CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    aggregate_id UUID,
    aggregate_type VARCHAR(100),
    event_type VARCHAR(100) NOT NULL,
    event_version INTEGER DEFAULT 1,
    payload JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 28. FILE MANAGEMENT (Enhanced)
-- ============================================================

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50),
    entity_id UUID,
    file_name VARCHAR(255),
    file_url TEXT,
    mime_type VARCHAR(100),
    file_size BIGINT,
    storage_provider VARCHAR(50) DEFAULT 'local',
    checksum VARCHAR(128),
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 29. SETTINGS SYSTEM
-- ============================================================

CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, key)
);

-- ============================================================
-- 30. MANUFACTURING MODULE
-- ============================================================

CREATE TABLE bill_of_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    material_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE production_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE RESTRICT,
    quantity NUMERIC(12, 2) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 31. HR MODULE
-- ============================================================

CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    employee_number VARCHAR(50),
    position VARCHAR(100),
    hire_date DATE,
    salary NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE leaves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payroll (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    base_salary NUMERIC(12, 2),
    deductions NUMERIC(12, 2) DEFAULT 0,
    bonuses NUMERIC(12, 2) DEFAULT 0,
    net_salary NUMERIC(12, 2),
    status VARCHAR(30) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 32. POS MODULE
-- ============================================================

CREATE TABLE pos_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    branch_id UUID REFERENCES branches(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    opening_balance NUMERIC(12, 2) DEFAULT 0,
    closing_balance NUMERIC(12, 2),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'open' CHECK (status IN ('open', 'closed'))
);

CREATE TABLE cash_drawers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pos_session_id UUID REFERENCES pos_sessions(id) ON DELETE CASCADE,
    action VARCHAR(30) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 33. SAAS SUBSCRIPTION SYSTEM
-- ============================================================

CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    max_users INTEGER,
    max_branches INTEGER,
    features JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES subscription_plans(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(30) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'trial')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 34. FEATURE FLAGS
-- ============================================================

CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 35. WEBHOOKS
-- ============================================================

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    target_url TEXT NOT NULL,
    secret_key_hash TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 36. SCHEDULED REPORTS
-- ============================================================

CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    report_name VARCHAR(255) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    recipient_email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 37. BACKGROUND JOBS
-- ============================================================

CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    job_type VARCHAR(100) NOT NULL,
    payload JSONB,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- ============================================================
-- 38. API RATE LIMITING
-- ============================================================

CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 39. BUSINESS INTELLIGENCE
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
-- 40. SYSTEM HEALTH & BACKUP
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
-- 41. DATABASE MIGRATION TRACKING
-- ============================================================

CREATE TABLE schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    applied_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 42. DATA RETENTION
-- ============================================================

CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL,
    archive_strategy VARCHAR(30) DEFAULT 'soft_delete',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
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
-- INDEXES
-- ============================================================

-- Tenants
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

-- Products
CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_search ON products USING GIN(search_vector);
CREATE INDEX idx_barcodes_product ON barcodes(product_id);
CREATE INDEX idx_product_units_product ON product_units(product_id);

-- Inventory
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_movements_tenant ON inventory_movements(tenant_id);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_inventory_batches_product ON inventory_batches(product_id);
CREATE INDEX idx_inventory_batches_expiry ON inventory_batches(expiry_date);

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
CREATE INDEX idx_sales_items_invoice ON sales_items(invoice_id);
CREATE INDEX idx_sales_items_product ON sales_items(product_id);

-- Purchases
CREATE INDEX idx_purchase_invoices_tenant ON purchase_invoices(tenant_id);
CREATE INDEX idx_purchase_invoices_company ON purchase_invoices(company_id);
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_invoices_branch ON purchase_invoices(branch_id);
CREATE INDEX idx_purchase_items_invoice ON purchase_items(invoice_id);

-- Payments & Treasury
CREATE INDEX idx_payments_tenant ON payments(tenant_id);
CREATE INDEX idx_payments_company ON payments(company_id);
CREATE INDEX idx_payments_treasury ON payments(treasury_id);
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

-- Semantic Search (Vector)
CREATE INDEX idx_ai_embedding ON ai_logs USING ivfflat (embedding vector_cosine_ops);

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

-- Warehouses
CREATE INDEX idx_warehouses_tenant ON warehouses(tenant_id);
CREATE INDEX idx_warehouses_company ON warehouses(company_id);
CREATE INDEX idx_warehouses_branch ON warehouses(branch_id);

-- Webhooks
CREATE INDEX idx_webhooks_tenant ON webhooks(tenant_id);
CREATE INDEX idx_webhooks_event ON webhooks(event_type);

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

-- ============================================================
-- SEED DATA
-- ============================================================

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

-- Default Permissions (Module.Action.Scope format)
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

-- Schema version tracking
INSERT INTO schema_migrations (version, name) VALUES
    ('v4.0.0', 'Enterprise SaaS schema with full tenant isolation');
