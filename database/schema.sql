-- Ceramix AI ERP - Database Schema
-- PostgreSQL Database
-- UUID-based, normalized, transaction-safe architecture

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. AUTHENTICATION MODULE
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
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
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
-- 2. CRM MODULE
-- ============================================================

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    credit_limit NUMERIC(12, 2) DEFAULT 0,
    balance NUMERIC(12, 2) DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(200) NOT NULL,
    phone VARCHAR(30),
    balance NUMERIC(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 3. PRODUCTS MODULE
-- ============================================================

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE,
    category VARCHAR(100),
    unit VARCHAR(30) DEFAULT 'piece',
    sale_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    purchase_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
    average_cost NUMERIC(12, 2) DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 4. WAREHOUSE MODULE
-- ============================================================

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id UUID NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(product_id, warehouse_id)
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    from_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    to_warehouse_id UUID REFERENCES warehouses(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    reason VARCHAR(50) NOT NULL CHECK (reason IN ('purchase', 'sale', 'transfer', 'return', 'adjustment')),
    reference_id UUID,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 5. SALES MODULE
-- ============================================================

CREATE TABLE sales_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    payment_type VARCHAR(30) DEFAULT 'cash',
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'partial', 'cancelled')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE sales_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES sales_invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    discount NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL
);

-- ============================================================
-- 6. PURCHASE MODULE
-- ============================================================

CREATE TABLE purchase_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    supplier_id UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    total NUMERIC(12, 2) NOT NULL DEFAULT 0,
    amount_paid NUMERIC(12, 2) DEFAULT 0,
    status VARCHAR(30) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'partial', 'cancelled')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE purchase_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);

-- ============================================================
-- 7. TREASURY & FINANCE MODULE
-- ============================================================

CREATE TABLE treasury (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    balance NUMERIC(14, 2) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'EGP',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sales_invoice_id UUID REFERENCES sales_invoices(id) ON DELETE SET NULL,
    purchase_invoice_id UUID REFERENCES purchase_invoices(id) ON DELETE SET NULL,
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    amount NUMERIC(12, 2) NOT NULL,
    method VARCHAR(30) NOT NULL CHECK (method IN ('cash', 'bank_transfer', 'cheque')),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    treasury_id UUID NOT NULL REFERENCES treasury(id) ON DELETE RESTRICT,
    category VARCHAR(50) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    description TEXT,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 8. RETURNS MODULE
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
-- 9. AI & ANALYTICS MODULE
-- ============================================================

CREATE TABLE ai_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_query TEXT,
    generated_sql TEXT,
    ai_response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- 10. AUDIT & MONITORING MODULE
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    table_name VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES (Performance Optimization)
-- ============================================================

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);

-- Customers & Suppliers
CREATE INDEX idx_customers_name ON customers(full_name);
CREATE INDEX idx_suppliers_name ON suppliers(company_name);

-- Products
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category);

-- Inventory
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
CREATE INDEX idx_inventory_movements_reason ON inventory_movements(reason);

-- Sales
CREATE INDEX idx_sales_invoices_customer ON sales_invoices(customer_id);
CREATE INDEX idx_sales_invoices_status ON sales_invoices(status);
CREATE INDEX idx_sales_invoices_date ON sales_invoices(created_at);
CREATE INDEX idx_sales_items_invoice ON sales_items(invoice_id);
CREATE INDEX idx_sales_items_product ON sales_items(product_id);

-- Purchases
CREATE INDEX idx_purchase_invoices_supplier ON purchase_invoices(supplier_id);
CREATE INDEX idx_purchase_items_invoice ON purchase_items(invoice_id);

-- Payments
CREATE INDEX idx_payments_treasury ON payments(treasury_id);
CREATE INDEX idx_payments_sales ON payments(sales_invoice_id);
CREATE INDEX idx_payments_purchases ON payments(purchase_invoice_id);

-- Audit
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);

-- ============================================================
-- SEED DATA (Default Roles & Permissions)
-- ============================================================

INSERT INTO roles (name, description) VALUES
    ('admin', 'Full system access'),
    ('accountant', 'Financial operations and reporting'),
    ('sales', 'Sales and customer management'),
    ('warehouse', 'Inventory and stock management');

INSERT INTO permissions (name, description) VALUES
    ('create_invoice', 'Create sales/purchase invoices'),
    ('manage_inventory', 'Manage stock and warehouses'),
    ('view_reports', 'View financial and analytics reports'),
    ('manage_users', 'Create and manage system users'),
    ('manage_treasury', 'Manage treasury and payments'),
    ('manage_returns', 'Process sales and purchase returns'),
    ('view_audit_logs', 'View system audit logs'),
    ('ai_query', 'Use AI query features');
