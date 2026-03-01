PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    country TEXT NOT NULL,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'pro', 'team')),
    plan_id TEXT NOT NULL CHECK (plan_id IN ('free', 'pro', 'team')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    salary NUMERIC NOT NULL,
    hired_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    phone TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    discount NUMERIC,
    discount_value NUMERIC,
    created_at TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('new', 'paid', 'shipped', 'cancelled')),
    total NUMERIC NOT NULL,
    total_amount NUMERIC NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    author_id INTEGER NOT NULL,
    author_user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    published_at TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (author_user_id) REFERENCES users(id)
);

CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_users_plan_active ON users(plan, is_active);
CREATE INDEX idx_users_planid_active ON users(plan_id, active);
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_products_category_price ON products(category_id, price DESC);
CREATE INDEX idx_orders_customer_created_at ON orders(customer_id, created_at);
CREATE INDEX idx_orders_user_created_at ON orders(user_id, created_at);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_employees_department_salary ON employees(department_id, salary DESC);
CREATE INDEX idx_articles_author ON articles(author_id, published_at);
