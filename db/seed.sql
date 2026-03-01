PRAGMA foreign_keys = ON;

INSERT INTO users (id, email, full_name, country, plan, plan_id, is_active, active, created_at, deleted_at) VALUES
(1, 'anna.kowalska@example.com', 'Anna Kowalska', 'Poland', 'pro', 'pro', 1, 1, '2024-01-10', NULL),
(2, 'piotr.nowak@example.com', 'Piotr Nowak', 'Poland', 'free', 'free', 1, 1, '2024-01-14', NULL),
(3, 'maria.zielinska@example.com', 'Maria Zielinska', 'Germany', 'team', 'team', 1, 1, '2024-02-02', NULL),
(4, 'jan.wisniewski@example.com', 'Jan Wisniewski', 'Poland', 'free', 'free', 0, 0, '2024-02-15', '2025-01-03'),
(5, 'emilia.wojcik@example.com', 'Emilia Wojcik', 'Czechia', 'pro', 'pro', 1, 1, '2024-03-01', NULL),
(6, 'tomasz.krawczyk@example.com', 'Tomasz Krawczyk', 'Germany', 'free', 'free', 1, 1, '2024-03-22', NULL),
(7, 'aleksandra.dabrowska@example.com', 'Aleksandra Dabrowska', 'France', 'team', 'team', 1, 1, '2024-04-03', NULL),
(8, 'lukasz.lewandowski@example.com', 'Lukasz Lewandowski', 'Poland', 'pro', 'pro', 1, 1, '2024-04-18', NULL),
(9, 'zofia.kaminska@example.com', 'Zofia Kaminska', 'Spain', 'free', 'free', 1, 1, '2024-05-02', NULL),
(10, 'mateusz.szymanski@example.com', 'Mateusz Szymanski', 'Poland', 'team', 'team', 1, 1, '2024-05-15', NULL);

INSERT INTO departments (id, name, active) VALUES
(1, 'Sales', 1),
(2, 'Engineering', 1),
(3, 'Support', 1),
(4, 'Finance', 0);

INSERT INTO employees (id, user_id, department_id, salary, hired_at) VALUES
(1, 1, 2, 14500, '2023-03-01'),
(2, 2, 1, 9800, '2023-07-10'),
(3, 3, 2, 16200, '2022-11-18'),
(4, 5, 3, 9200, '2024-01-11'),
(5, 7, 1, 11100, '2023-09-22'),
(6, 8, 2, 13400, '2024-02-04'),
(7, 10, 3, 8700, '2024-05-30');

INSERT INTO customers (id, user_id, name, city, phone, created_at) VALUES
(1, 1, 'Anna Kowalska', 'Warsaw', '+48-500-111-222', '2024-01-11'),
(2, 2, 'Piotr Nowak', 'Krakow', NULL, '2024-01-16'),
(3, 3, 'Maria Zielinska', 'Berlin', '+49-170-000-123', '2024-02-05'),
(4, 5, 'Emilia Wojcik', 'Prague', '+420-601-222-333', '2024-03-03'),
(5, 6, 'Tomasz Krawczyk', 'Munich', NULL, '2024-03-24'),
(6, 8, 'Lukasz Lewandowski', 'Warsaw', '+48-501-987-654', '2024-04-20'),
(7, 9, 'Zofia Kaminska', 'Madrid', '+34-600-111-999', '2024-05-04'),
(8, 10, 'Mateusz Szymanski', 'Gdansk', NULL, '2024-05-16');

INSERT INTO categories (id, name) VALUES
(1, 'Electronics'),
(2, 'Home'),
(3, 'Books'),
(4, 'Sports');

INSERT INTO products (id, category_id, name, price, discount, discount_value, created_at) VALUES
(1, 1, 'Laptop Pro 14', 6499, 500, 500, '2024-01-01'),
(2, 1, 'Wireless Headphones', 599, NULL, NULL, '2024-01-08'),
(3, 1, 'Mechanical Keyboard', 429, 30, 30, '2024-02-12'),
(4, 2, 'Air Purifier', 899, 120, 120, '2024-02-20'),
(5, 2, 'Standing Desk', 1499, NULL, NULL, '2024-03-15'),
(6, 3, 'SQL in Practice', 119, 20, 20, '2024-03-18'),
(7, 3, 'Data Engineering 101', 139, NULL, NULL, '2024-04-01'),
(8, 4, 'Trail Running Shoes', 469, 40, 40, '2024-04-12'),
(9, 4, 'Yoga Mat', 149, NULL, NULL, '2024-04-16'),
(10, 1, '4K Monitor', 1899, 150, 150, '2024-05-01');

INSERT INTO orders (id, user_id, customer_id, status, total, total_amount, created_at) VALUES
(1, 1, 1, 'paid', 7098, 7098, '2024-06-01'),
(2, 2, 2, 'shipped', 119, 119, '2024-06-02'),
(3, 3, 3, 'paid', 2048, 2048, '2024-06-03'),
(4, 1, 1, 'new', 469, 469, '2024-06-07'),
(5, 5, 4, 'paid', 1499, 1499, '2024-06-11'),
(6, 6, 5, 'cancelled', 599, 599, '2024-06-12'),
(7, 8, 6, 'shipped', 1018, 1018, '2024-06-15'),
(8, 10, 8, 'paid', 2278, 2278, '2024-06-19'),
(9, 9, 7, 'paid', 288, 288, '2024-06-23'),
(10, 3, 3, 'new', 1899, 1899, '2024-06-29'),
(11, 1, 1, 'paid', 857, 857, '2024-07-01'),
(12, 2, 2, 'paid', 6468, 6468, '2024-07-05');

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1, 6499),
(2, 1, 2, 1, 599),
(3, 2, 6, 1, 119),
(4, 3, 10, 1, 1899),
(5, 3, 7, 1, 139),
(6, 4, 8, 1, 469),
(7, 5, 5, 1, 1499),
(8, 6, 2, 1, 599),
(9, 7, 4, 1, 899),
(10, 7, 9, 1, 149),
(11, 8, 10, 1, 1899),
(12, 8, 3, 1, 379),
(13, 9, 6, 2, 99),
(14, 9, 9, 1, 90),
(15, 10, 10, 1, 1899),
(16, 11, 3, 2, 429),
(17, 12, 1, 1, 6399),
(18, 12, 6, 1, 69);

INSERT INTO articles (id, author_id, author_user_id, title, published_at) VALUES
(1, 1, 1, 'SQL joins in practice', '2024-01-05'),
(2, 1, 1, 'Understanding GROUP BY', '2024-02-10'),
(3, 1, 1, 'Window functions for analysts', '2024-04-20'),
(4, 2, 2, 'SQLite basics', '2024-01-20'),
(5, 3, 3, 'Optimizing indexes', '2024-03-11'),
(6, 3, 3, 'CTE patterns', '2024-05-03'),
(7, 3, 3, 'Advanced ranking queries', '2024-06-02'),
(8, 5, 5, 'NULL handling guide', '2024-02-24'),
(9, 7, 7, 'Practical subqueries', '2024-05-15');
