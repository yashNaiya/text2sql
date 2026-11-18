# Execution accuracy - qwen2.5-coder:3b - role Admin

`{"model": "qwen2.5-coder:3b", "role": "Admin", "embedder": "sentence-transformers", "k": 3, "configs": ["llm_only", "schema", "schema_rag"], "date": "20261004_221403", "dry_run": false}`

### llm_only (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 |  10.0% |  10.0% | ** 10.0%** | 0 | 0 |
| medium | 10 |   0.0% |   0.0% | **  0.0%** | 0 | 0 |
| hard | 10 |  10.0% |   0.0% | **  0.0%** | 0 | 0 |
| overall | 30 |   6.7% |   3.3% | **  3.3%** | 0 | 0 |

avg latency 7544 ms, avg prompt ~75 tokens

### schema (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| medium | 10 | 100.0% |  80.0% | ** 30.0%** | 0 | 0 |
| hard | 10 |  70.0% |  60.0% | ** 10.0%** | 0 | 0 |
| overall | 30 |  90.0% |  80.0% | ** 46.7%** | 0 | 0 |

avg latency 3524 ms, avg prompt ~1343 tokens

### schema_rag (N=30)

| difficulty | n | valid SQL | executes | exec. accuracy | refused | blocked |
|---|---|---|---|---|---|---|
| easy | 10 | 100.0% | 100.0% | **100.0%** | 0 | 0 |
| medium | 10 | 100.0% | 100.0% | ** 90.0%** | 0 | 0 |
| hard | 10 | 100.0% | 100.0% | ** 50.0%** | 0 | 0 |
| overall | 30 | 100.0% | 100.0% | ** 80.0%** | 0 | 0 |

avg latency 3737 ms, avg prompt ~1532 tokens

## Failures

### llm_only: 29 failed

- **e02e** (easy) invalid - unknown column: status
  - Q: How many orders currently have the status shipped?
  - predicted: `SELECT COUNT(*) FROM orders WHERE status = 'shipped'`
  - gold: `SELECT COUNT(*) FROM orders WHERE order_status = 'shipped';`
- **e03e** (easy) invalid - unknown column: city
  - Q: How many different cities do sellers come from?
  - predicted: `SELECT COUNT(DISTINCT city) FROM sellers`
  - gold: `SELECT COUNT(DISTINCT seller_city) FROM sellers;`
- **e04e** (easy) invalid - unknown table: items
  - Q: What is the average price of an item sold?
  - predicted: `SELECT AVG(price) FROM items;`
  - gold: `SELECT AVG(price) FROM order_items;`
- **e05e** (easy) invalid - unknown table: payments
  - Q: What is the total value of all payments?
  - predicted: `SELECT SUM(amount) AS total_value FROM payments`
  - gold: `SELECT SUM(payment_value) FROM order_payments;`
- **e06e** (easy) invalid - unknown column: state
  - Q: How many sellers are located in the state of RJ?
  - predicted: `SELECT COUNT(*) FROM sellers WHERE state = 'RJ'`
  - gold: `SELECT COUNT(*) FROM sellers WHERE seller_state = 'RJ';`
- **e07e** (easy) invalid - unknown column: weight
  - Q: What is the weight in grams of the heaviest product?
  - predicted: `SELECT MAX(weight) AS heaviest_product_weight FROM products`
  - gold: `SELECT MAX(product_weight_g) FROM products;`
- **e08e** (easy) invalid - unknown column: state
  - Q: List all distinct customer states.
  - predicted: `SELECT DISTINCT state FROM customers;`
  - gold: `SELECT DISTINCT customer_state FROM customers;`
- **e09e** (easy) invalid - unknown column: order_date
  - Q: How many orders were placed in March 2018?
  - predicted: `SELECT COUNT(*) FROM orders WHERE strftime('%Y-%m', order_date) = '2018-03'`
  - gold: `SELECT COUNT(*) FROM orders WHERE strftime('%Y-%m', order_purchase_timestamp) = '2018-03';`
- **e10e** (easy) invalid - unknown table: reviews
  - Q: How many reviews have a score of 2 or lower?
  - predicted: `SELECT COUNT(*) FROM reviews WHERE score <= 2`
  - gold: `SELECT COUNT(*) FROM order_reviews WHERE review_score <= 2;`
- **m01e** (medium) invalid - unknown column: state
  - Q: How many customers are there in each state, from most to least?
  - predicted: `SELECT state, COUNT(*) AS customer_count FROM customers GROUP BY state ORDER BY customer_count DESC`
  - gold: `SELECT customer_state, COUNT(*) AS n FROM customers GROUP BY customer_state ORDER BY n DESC, customer_state;`
- **m02e** (medium) invalid - unknown column: id
  - Q: How many orders were placed by customers living in the state of RJ?
  - predicted: `SELECT COUNT(*) AS order_count
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE customers.state = 'RJ';`
  - gold: `SELECT COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.customer_state = 'RJ';`
- **m03e** (medium) invalid - unknown table: categories
  - Q: Which 3 product categories have the most items sold? Use the English category names.
  - predicted: `SELECT category_name, COUNT(*) AS item_count
FROM products
JOIN categories ON products.category_id = categories.id
GROUP BY category_name
ORDER BY item_count DESC
LIMIT 3;`
  - gold: `SELECT t.product_category_name_english AS category, COUNT(*) AS items_sold FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY category ORDER BY items_sold DESC, category LIMIT 3;`
- **m04e** (medium) invalid - unknown column: seller_state
  - Q: What is the average freight value for each seller state?
  - predicted: `SELECT seller_state, AVG(freight_value) AS average_freight_value
FROM orders
GROUP BY seller_state;`
  - gold: `SELECT s.seller_state, AVG(oi.freight_value) AS avg_freight FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id GROUP BY s.seller_state ORDER BY avg_freight DESC, s.seller_state;`
- **m05e** (medium) invalid - unknown table: sales
  - Q: What was the total item revenue in each month of 2018?
  - predicted: `SELECT strftime('%Y-%m', date_column) AS month, SUM(item_revenue) AS total_revenue
FROM sales
WHERE strftime('%Y', date_column) = '2018'
GROUP BY month;`
  - gold: `SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE strftime('%Y', o.order_purchase_timestamp) = '2018' GROUP BY month ORDER BY month;`
- **m06e** (medium) invalid - unknown table: sales
  - Q: Which products have been sold more than 100 times?
  - predicted: `SELECT product_id, COUNT(*) AS sales_count
FROM sales
GROUP BY product_id
HAVING sales_count > 100;`
  - gold: `SELECT product_id, COUNT(*) AS times_sold FROM order_items GROUP BY product_id HAVING COUNT(*) > 100 ORDER BY times_sold DESC, product_id;`
- **m07e** (medium) invalid - unknown column: freight_value
  - Q: What is the total freight value of canceled orders?
  - predicted: `SELECT SUM(freight_value) AS total_freight_value FROM orders WHERE status = 'canceled'`
  - gold: `SELECT SUM(oi.freight_value) FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE o.order_status = 'canceled';`
- **m08e** (medium) invalid - unknown column: status
  - Q: How many delivered orders arrived after the estimated delivery date?
  - predicted: `SELECT COUNT(*) 
FROM orders 
WHERE status = 'delivered' 
  AND arrival_date > estimated_delivery_date;`
  - gold: `SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL AND order_delivered_customer_date > order_estimated_delivery_date;`
- **m09e** (medium) invalid - unknown table: sales
  - Q: List the 5 sellers with the highest total revenue.
  - predicted: `SELECT seller_id, SUM(revenue) AS total_revenue
FROM sales
GROUP BY seller_id
ORDER BY total_revenue DESC
LIMIT 5;`
  - gold: `SELECT seller_id, SUM(price) AS revenue FROM order_items GROUP BY seller_id ORDER BY revenue DESC, seller_id LIMIT 5;`
- **m10e** (medium) invalid - unknown table: payments
  - Q: What is the total payment value for each payment type?
  - predicted: `SELECT payment_type, SUM(payment_value) AS total_payment_value
FROM payments
GROUP BY payment_type;`
  - gold: `SELECT payment_type, SUM(payment_value) AS total FROM order_payments GROUP BY payment_type ORDER BY total DESC, payment_type;`
- **h01e** (hard) invalid - unknown table: sales
  - Q: Which 10 sellers have total revenue above the average seller revenue?
  - predicted: `SELECT seller_id, SUM(revenue) AS total_revenue
FROM sales
GROUP BY seller_id
HAVING total_revenue > (SELECT AVG(total_revenue) FROM (SELECT SUM(revenue) AS total_revenue FROM sales GROUP BY seller_id))
ORDER BY total_revenue DESC
LIMIT 10;`
  - gold: `SELECT seller_id, SUM(price) AS revenue FROM order_items GROUP BY seller_id HAVING SUM(price) > (SELECT AVG(r) FROM (SELECT SUM(price) AS r FROM order_items GROUP BY seller_id)) ORDER BY revenue DESC, seller_id LIMIT 10;`
- **h02e** (hard) invalid - unknown table: sales
  - Q: For each seller state, which product category (English name) has the most items sold?
  - predicted: `SELECT s.state, p.category_name
FROM sellers s
JOIN products p ON s.id = p.seller_id
JOIN sales sa ON p.id = sa.product_id
GROUP BY s.state, p.category_name
ORDER BY COUNT(sa.id) DESC
LIMIT 1;`
  - gold: `WITH x AS (SELECT s.seller_state AS state, t.product_category_name_english AS category, COUNT(*) AS items FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY state, category), ranked AS (SELECT state, category, items, ROW_NUMBER() OVER `
- **h03e** (hard) invalid - unknown table: sales
  - Q: What is the month-over-month change in total item revenue during 2018?
  - predicted: `SELECT 
    strftime('%Y-%m', date) AS month,
    SUM(total_item_revenue) AS total_revenue
FROM 
    sales
WHERE 
    strftime('%Y', date) = '2018'
GROUP BY 
    strftime('%Y-%m', date)
ORDER BY 
    month;`
  - gold: `WITH m AS (SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE strftime('%Y', o.order_purchase_timestamp) = '2018' GROUP BY month) SELECT month, revenue, revenue - LAG(revenue) OVER (ORDER BY month) AS change FROM m ORDER BY month;`
- **h04e** (hard) invalid - unknown column: status
  - Q: How many delivered orders have no payment record?
  - predicted: `SELECT COUNT(*) FROM orders WHERE status = 'delivered' AND payment_record_id IS NULL`
  - gold: `SELECT COUNT(*) FROM orders o LEFT JOIN order_payments p ON o.order_id = p.order_id WHERE o.order_status = 'delivered' AND p.order_id IS NULL;`
- **h05e** (hard) exec_error - OperationalError: misuse of aggregate function COUNT()
  - Q: What percentage of unique customers placed more than one order?
  - predicted: `SELECT CAST(COUNT(CASE WHEN COUNT(*) > 1 THEN 1 END) AS REAL) * 100 / COUNT(DISTINCT customer_id) AS percentage
FROM orders;`
  - gold: `SELECT ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM (SELECT c.customer_unique_id, COUNT(o.order_id) AS n FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_unique_id);`
- **h06e** (hard) invalid - unknown column: delivery_status
  - Q: What percentage of delivered orders arrived late in each year?
  - predicted: `SELECT 
    strftime('%Y', delivery_date) AS year,
    COUNT(CASE WHEN delivery_status = 'Late' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) AS late_percentage
FROM 
    orders
WHERE 
    delivery_status = 'Delivered'
GROUP BY 
    year;`
  - gold: `SELECT strftime('%Y', order_purchase_timestamp) AS year, ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_pct FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL GROUP BY year ORDER BY year;`
- **h07e** (hard) invalid - unknown table: reviews
  - Q: What is the average delivery time in days for each review score?
  - predicted: `SELECT review_score, AVG(delivery_time) AS average_delivery_time
FROM reviews
GROUP BY review_score;`
  - gold: `SELECT r.review_score, AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_days FROM orders o JOIN order_reviews r ON o.order_id = r.order_id WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL GROUP BY r.review_score ORDER BY r.review_score;`
- **h08e** (hard) invalid - unknown table: sales
  - Q: Which product category (English name) had the highest revenue in 2018, and what was that revenue?
  - predicted: `SELECT T2.category_name, SUM(T1.total_revenue) AS total_revenue
FROM sales AS T1
JOIN products AS T2 ON T1.product_id = T2.product_id
WHERE strftime('%Y', T1.sale_date) = '2018'
GROUP BY T2.category_name
ORDER BY total_revenue DESC
LIMIT 1`
  - gold: `SELECT t.product_category_name_english AS category, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name WHERE strftime('%Y', o.order_purchase_timestamp) = '2018' GROUP BY category ORDER BY revenue DESC, category LIMIT 1;`
- **h09e** (hard) invalid - unknown table: reviews
  - Q: Which product category (English name) has the lowest average review score among categories with at least 100 reviews?
  - predicted: `SELECT T2.category_name
FROM reviews AS T1
JOIN products AS T2 ON T1.product_id = T2.product_id
GROUP BY T2.category_name
HAVING COUNT(T1.review_id) >= 100
ORDER BY AVG(T1.review_score) ASC
LIMIT 1;`
  - gold: `SELECT t.product_category_name_english AS category, AVG(r.review_score) AS avg_score, COUNT(*) AS n FROM order_reviews r JOIN order_items oi ON r.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY category HAVING COUNT(*) >= 100 ORDER BY avg_score ASC, category LIMIT 1;`
- **h10e** (hard) invalid - unknown column: item_revenue
  - Q: Show the cumulative item revenue by month over the whole dataset.
  - predicted: `SELECT strftime('%Y-%m', order_date) AS month, SUM(item_revenue) AS cumulative_revenue
FROM orders
GROUP BY month
ORDER BY month;`
  - gold: `WITH m AS (SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id GROUP BY month) SELECT month, revenue, SUM(revenue) OVER (ORDER BY month) AS cumulative FROM m ORDER BY month;`

### schema: 16 failed

- **m01e** (medium) exec_error - OperationalError: no such column: T2.customer_state
  - Q: How many customers are there in each state, from most to least?
  - predicted: `SELECT T2.customer_state, COUNT(T1.customer_unique_id) AS customer_count FROM customers AS T1 INNER JOIN orders AS T2 ON T1.customer_id = T2.customer_id GROUP BY T2.customer_state ORDER BY customer_count DESC`
  - gold: `SELECT customer_state, COUNT(*) AS n FROM customers GROUP BY customer_state ORDER BY n DESC, customer_state;`
- **m03e** (medium) exec_error - OperationalError: no such column: T2.product_category_name_english
  - Q: Which 3 product categories have the most items sold? Use the English category names.
  - predicted: `SELECT T2.product_category_name_english, COUNT(T1.order_item_id) AS item_count
FROM order_items AS T1
JOIN products AS T2 ON T1.product_id = T2.product_id
JOIN product_category_name_translation AS T3 ON T2.product_category_name = T3.product_category_name
GROUP BY T2.product_category_name_english
ORDER BY item_count DESC
LIMIT 3`
  - gold: `SELECT t.product_category_name_english AS category, COUNT(*) AS items_sold FROM order_items oi JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY category ORDER BY items_sold DESC, category LIMIT 3;`
- **m04e** (medium) ok
  - Q: What is the average freight value for each seller state?
  - predicted: `SELECT T2.seller_state, AVG(T1.freight_value) AS average_freight_value
FROM order_items AS T1
JOIN sellers AS T2 ON T1.seller_id = T2.seller_id
GROUP BY T2.seller_state`
  - gold: `SELECT s.seller_state, AVG(oi.freight_value) AS avg_freight FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id GROUP BY s.seller_state ORDER BY avg_freight DESC, s.seller_state;`
- **m06e** (medium) ok
  - Q: Which products have been sold more than 100 times?
  - predicted: `SELECT p.product_id, COUNT(*) AS sales_count
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id
HAVING sales_count > 100`
  - gold: `SELECT product_id, COUNT(*) AS times_sold FROM order_items GROUP BY product_id HAVING COUNT(*) > 100 ORDER BY times_sold DESC, product_id;`
- **m08e** (medium) ok
  - Q: How many delivered orders arrived after the estimated delivery date?
  - predicted: `SELECT COUNT(order_id) FROM orders WHERE order_status = 'delivered' AND strftime('%Y-%m-%d', order_delivered_customer_date) > strftime('%Y-%m-%d', order_estimated_delivery_date)`
  - gold: `SELECT COUNT(*) FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL AND order_delivered_customer_date > order_estimated_delivery_date;`
- **m09e** (medium) ok
  - Q: List the 5 sellers with the highest total revenue.
  - predicted: `SELECT s.seller_id, SUM(oi.price + oi.freight_value) AS total_revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
GROUP BY s.seller_id
ORDER BY total_revenue DESC
LIMIT 5`
  - gold: `SELECT seller_id, SUM(price) AS revenue FROM order_items GROUP BY seller_id ORDER BY revenue DESC, seller_id LIMIT 5;`
- **m10e** (medium) ok
  - Q: What is the total payment value for each payment type?
  - predicted: `SELECT payment_type, SUM(payment_value) AS total_payment_value FROM order_payments GROUP BY payment_type`
  - gold: `SELECT payment_type, SUM(payment_value) AS total FROM order_payments GROUP BY payment_type ORDER BY total DESC, payment_type;`
- **h01e** (hard) ok
  - Q: Which 10 sellers have total revenue above the average seller revenue?
  - predicted: `SELECT s.seller_id, SUM(o.price + o.freight_value) AS total_revenue
FROM order_items o
JOIN sellers s ON o.seller_id = s.seller_id
GROUP BY s.seller_id
HAVING total_revenue > (SELECT AVG(total_revenue) FROM (SELECT SUM(price + freight_value) AS total_revenue
FROM order_items
JOIN sellers ON order_items.seller_id = sellers.seller_id
GROUP BY sellers.seller_id))`
  - gold: `SELECT seller_id, SUM(price) AS revenue FROM order_items GROUP BY seller_id HAVING SUM(price) > (SELECT AVG(r) FROM (SELECT SUM(price) AS r FROM order_items GROUP BY seller_id)) ORDER BY revenue DESC, seller_id LIMIT 10;`
- **h02e** (hard) exec_error - OperationalError: no such column: T2.product_category_name_english
  - Q: For each seller state, which product category (English name) has the most items sold?
  - predicted: `SELECT T2.product_category_name_english, COUNT(T1.product_id) AS item_count
FROM order_items AS T1
JOIN products AS T2 ON T1.product_id = T2.product_id
JOIN product_category_name_translation AS T3 ON T2.product_category_name = T3.product_category_name
GROUP BY T3.product_category_name_english
ORDER BY item_count DESC
LIMIT 1`
  - gold: `WITH x AS (SELECT s.seller_state AS state, t.product_category_name_english AS category, COUNT(*) AS items FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY state, category), ranked AS (SELECT state, category, items, ROW_NUMBER() OVER `
- **h03e** (hard) ok
  - Q: What is the month-over-month change in total item revenue during 2018?
  - predicted: `SELECT strftime('%Y-%m', order_purchase_timestamp) AS month, SUM(price) AS total_revenue
FROM orders
JOIN order_items ON orders.order_id = order_items.order_id
WHERE strftime('%Y', order_purchase_timestamp) BETWEEN '2018-01' AND '2018-12'
GROUP BY month
ORDER BY month`
  - gold: `WITH m AS (SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id WHERE strftime('%Y', o.order_purchase_timestamp) = '2018' GROUP BY month) SELECT month, revenue, revenue - LAG(revenue) OVER (ORDER BY month) AS change FROM m ORDER BY month;`
- **h05e** (hard) ok
  - Q: What percentage of unique customers placed more than one order?
  - predicted: `SELECT CAST(COUNT(DISTINCT T1.customer_unique_id) AS REAL) * 100 / COUNT(T1.customer_id) FROM customers AS T1 INNER JOIN orders AS T2 ON T1.customer_id = T2.customer_id GROUP BY T1.customer_unique_id HAVING COUNT(T2.order_id) > 1`
  - gold: `SELECT ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM (SELECT c.customer_unique_id, COUNT(o.order_id) AS n FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_unique_id);`
- **h06e** (hard) ok
  - Q: What percentage of delivered orders arrived late in each year?
  - predicted: `SELECT strftime('%Y', o.order_delivered_customer_date) AS year, COUNT(CASE WHEN o.order_delivered_customer_date < o.order_estimated_delivery_date THEN 1 ELSE NULL END) * 100.0 / COUNT(o.order_id) AS late_percentage
FROM orders o
WHERE o.order_status = 'delivered'
GROUP BY year`
  - gold: `SELECT strftime('%Y', order_purchase_timestamp) AS year, ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_pct FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL GROUP BY year ORDER BY year;`
- **h07e** (hard) ok
  - Q: What is the average delivery time in days for each review score?
  - predicted: `SELECT AVG(strftime('%j', order_delivered_customer_date) - strftime('%j', order_purchase_timestamp)) AS average_delivery_time, review_score FROM orders INNER JOIN order_reviews ON orders.order_id = order_reviews.order_id GROUP BY review_score`
  - gold: `SELECT r.review_score, AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_days FROM orders o JOIN order_reviews r ON o.order_id = r.order_id WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL GROUP BY r.review_score ORDER BY r.review_score;`
- **h08e** (hard) invalid - unknown column: order_purchase_timestamp
  - Q: Which product category (English name) had the highest revenue in 2018, and what was that revenue?
  - predicted: `SELECT T2.product_category_name_english, SUM(T1.price) AS total_revenue
FROM order_items AS T1
JOIN products AS T2 ON T1.product_id = T2.product_id
JOIN product_category_name_translation AS T3 ON T2.product_category_name = T3.product_category_name
WHERE strftime('%Y', T1.order_purchase_timestamp) = '2018'
GROUP BY T2.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 1`
  - gold: `SELECT t.product_category_name_english AS category, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name WHERE strftime('%Y', o.order_purchase_timestamp) = '2018' GROUP BY category ORDER BY revenue DESC, category LIMIT 1;`
- **h09e** (hard) invalid - unknown column: product_category_name_english
  - Q: Which product category (English name) has the lowest average review score among categories with at least 100 reviews?
  - predicted: `SELECT T2.product_category_name_english FROM order_reviews AS T1 INNER JOIN products AS T2 ON T1.order_id = T2.product_id GROUP BY T2.product_category_name_english HAVING COUNT(T1.review_id) >= 100 ORDER BY AVG(T1.review_score) ASC LIMIT 1`
  - gold: `SELECT t.product_category_name_english AS category, AVG(r.review_score) AS avg_score, COUNT(*) AS n FROM order_reviews r JOIN order_items oi ON r.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY category HAVING COUNT(*) >= 100 ORDER BY avg_score ASC, category LIMIT 1;`
- **h10e** (hard) invalid - unknown column: order_purchase_timestamp
  - Q: Show the cumulative item revenue by month over the whole dataset.
  - predicted: `SELECT strftime('%Y-%m', order_purchase_timestamp) AS month, SUM(price) AS cumulative_revenue
FROM order_items
GROUP BY month
ORDER BY month`
  - gold: `WITH m AS (SELECT strftime('%Y-%m', o.order_purchase_timestamp) AS month, SUM(oi.price) AS revenue FROM orders o JOIN order_items oi ON o.order_id = oi.order_id GROUP BY month) SELECT month, revenue, SUM(revenue) OVER (ORDER BY month) AS cumulative FROM m ORDER BY month;`

### schema_rag: 6 failed

- **m04e** (medium) ok
  - Q: What is the average freight value for each seller state?
  - predicted: `SELECT s.seller_state, AVG(oi.freight_value) AS average_freight_value
FROM sellers s
JOIN order_items oi ON s.seller_id = oi.seller_id
GROUP BY s.seller_state`
  - gold: `SELECT s.seller_state, AVG(oi.freight_value) AS avg_freight FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id GROUP BY s.seller_state ORDER BY avg_freight DESC, s.seller_state;`
- **h02e** (hard) ok
  - Q: For each seller state, which product category (English name) has the most items sold?
  - predicted: `SELECT s.seller_state, t.product_category_name_english AS category, COUNT(*) AS items_sold FROM sellers s JOIN order_items oi ON s.seller_id = oi.seller_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY s.seller_state, category ORDER BY s.seller_state, items_sold DESC`
  - gold: `WITH x AS (SELECT s.seller_state AS state, t.product_category_name_english AS category, COUNT(*) AS items FROM order_items oi JOIN sellers s ON oi.seller_id = s.seller_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY state, category), ranked AS (SELECT state, category, items, ROW_NUMBER() OVER `
- **h05e** (hard) ok
  - Q: What percentage of unique customers placed more than one order?
  - predicted: `SELECT COUNT(*) FROM (SELECT c.customer_unique_id FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_unique_id HAVING COUNT(o.order_id) > 1) AS unique_customers_with_multiple_orders;`
  - gold: `SELECT ROUND(100.0 * SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct FROM (SELECT c.customer_unique_id, COUNT(o.order_id) AS n FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_unique_id);`
- **h06e** (hard) ok
  - Q: What percentage of delivered orders arrived late in each year?
  - predicted: `SELECT strftime('%Y', o.order_purchase_timestamp) AS year, ROUND(100.0 * SUM(CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_pct FROM orders o WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL GROUP BY year ORDER BY late_pct DESC, year`
  - gold: `SELECT strftime('%Y', order_purchase_timestamp) AS year, ROUND(100.0 * SUM(CASE WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_pct FROM orders WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL GROUP BY year ORDER BY year;`
- **h07e** (hard) ok
  - Q: What is the average delivery time in days for each review score?
  - predicted: `SELECT AVG(julianday(order_delivered_customer_date) - julianday(order_purchase_timestamp)) AS avg_days, r.review_score FROM orders o JOIN order_reviews r ON o.order_id = r.order_id WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL GROUP BY r.review_score ORDER BY avg_days DESC, r.review_score`
  - gold: `SELECT r.review_score, AVG(julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS avg_days FROM orders o JOIN order_reviews r ON o.order_id = r.order_id WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL GROUP BY r.review_score ORDER BY r.review_score;`
- **h09e** (hard) ok
  - Q: Which product category (English name) has the lowest average review score among categories with at least 100 reviews?
  - predicted: `SELECT pcnt.product_category_name_english, AVG(r.review_score) AS avg_score FROM product_category_name_translation pcnt JOIN products p ON pcnt.product_category_name = p.product_category_name JOIN order_items oi ON p.product_id = oi.product_id JOIN order_reviews r ON oi.order_id = r.order_id GROUP BY pcnt.product_category_name_english HAVING COUNT(DISTINCT oi.order_id) >= 100 ORDER BY avg_score AS`
  - gold: `SELECT t.product_category_name_english AS category, AVG(r.review_score) AS avg_score, COUNT(*) AS n FROM order_reviews r JOIN order_items oi ON r.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id JOIN product_category_name_translation t ON p.product_category_name = t.product_category_name GROUP BY category HAVING COUNT(*) >= 100 ORDER BY avg_score ASC, category LIMIT 1;`
