# Mapowanie lekcji SQL do tabel i kolumn (dataset bazowy)

Poniższa mapa opisuje, które elementy bazy z `db/schema.sql` oraz `db/seed.sql` wspierają każdą lekcję.
Snapshot startowy jest tworzony warunkowo przez `./db/reset_session_db.sh` (domyślnie w `.runtime/sqlite/base_snapshot.sqlite`).

## Tabele bazowe

- `users`
- `departments`
- `employees`
- `customers`
- `categories`
- `products`
- `orders`
- `order_items`
- `articles`

## Zgodność z istniejącymi lekcjami

Aby utrzymać kompatybilność ze starszymi wzorcami odpowiedzi (`expectedQueryPatterns`) i jednocześnie czytelność domenową,
dataset zawiera równoległe kolumny kompatybilności:

- `users.active` oraz `users.is_active`
- `users.plan_id` oraz `users.plan`
- `orders.total` oraz `orders.total_amount`
- `products.discount` oraz `products.discount_value`
- `articles.author_id` oraz `articles.author_user_id`

## Mapowanie lekcji

| Lekcja | Tabele | Kluczowe kolumny |
|---|---|---|
| `01-select-basics` | `users`, `customers`, `products` | `users.id`, `users.email`, `customers.id`, `customers.name`, `products.*` |
| `02-where-filtering` | `products`, `orders`, `customers` | `products.price`, `orders.status`, `customers.city` |
| `03-order-by-sorting` | `employees`, `users`, `customers` | `employees.salary`, `users.created_at`, `customers.city`, `customers.name` |
| `04-limit-results` | `products` | `products.price`, `products.created_at` |
| `05-group-by-basics` | `users`, `orders`, `products` | `users.country`, `orders.status`, `products.category_id`, `products.price` |
| `06-having-filter-groups` | `articles`, `orders`, `products` | `articles.author_id`, `orders.customer_id`, `products.category_id`, `products.price` |
| `07-inner-join-basics` | `orders`, `customers`, `order_items` | `orders.id`, `orders.customer_id`, `customers.id`, `customers.name`, `order_items.order_id`, `order_items.quantity` |
| `08-subqueries-where` | `customers`, `orders`, `employees`, `departments`, `products` | `orders.customer_id`, `departments.id`, `departments.active`, `employees.department_id`, `products.price` |
| `09-subqueries-from` | `users`, `orders`, `products` | `users.country`, `orders.customer_id`, `products.category_id`, `products.price` |
| `10-cte-basics` | `users`, `orders`, `products` | `users.active`, `users.plan_id`, `orders.created_at`, `products.price` |
| `11-window-functions-rank` | `orders`, `employees` | `orders.customer_id`, `orders.created_at`, `employees.department_id`, `employees.salary` |
| `12-window-functions-running-total` | `orders` | `orders.created_at`, `orders.total`, `orders.customer_id` |
| `13-distinct-and-aliases` | `users`, `customers`, `orders` | `users.country`, `customers.city`, `orders.id`, `orders.customer_id` |
| `14-null-handling` | `products`, `users`, `customers` | `products.discount`, `products.discount_value`, `users.deleted_at`, `customers.phone` |
| `15-multi-table-joins` | `users`, `orders`, `order_items`, `products`, `customers` | `orders.user_id`, `orders.customer_id`, `order_items.quantity`, `order_items.unit_price`, `products.category_id` |
| `16-cte-and-window-top-n` | `employees`, `departments`, `orders`, `order_items`, `products` | `employees.department_id`, `employees.salary`, `orders.customer_id`, `orders.created_at`, agregacja sprzedaży po `order_items.product_id` + `products.category_id` |

## Uwagi o przykładach „koncepcyjnych”

W części lekcji występują krótkie przykłady dydaktyczne z nazwami tabel takimi jak `leaderboard`, `daily_sales` czy `posts`.
Nie są one częścią bazowego snapshotu i służą wyłącznie do pokazania składni.
Ćwiczenia wykonywalne oraz główna ścieżka kursu są pokryte przez 9 tabel zdefiniowanych w `db/schema.sql`.
