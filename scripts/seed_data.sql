-- Seed categories
INSERT INTO budget.categories (id, name, parent_id) VALUES
(1, '{"en": "Income", "ru": "Доход"}', NULL),
(2, '{"en": "Transfer", "ru": "Перевод"}', NULL),
(3, '{"en": "Food", "ru": "Еда"}', NULL),
(4, '{"en": "Housing", "ru": "Жилье"}', NULL),
(5, '{"en": "Transport", "ru": "Транспорт"}', NULL),
(6, '{"en": "Kids", "ru": "Дети"}', NULL),
(7, '{"en": "Lifestyle", "ru": "Личные расходы"}', NULL),
(8, '{"en": "Financial", "ru": "Финансы"}', NULL),
(9, '{"en": "Pets", "ru": "Питомцы"}', NULL),
(10, '{"en": "Gifts & Charity", "ru": "Подарки и благотворительность"}', NULL),
(11, '{"en": "Junk Food & Sweets", "ru": "Вредная еда и сладости"}', 3),
(12, '{"en": "Internet & Mobile", "ru": "Связь и интернет"}', 4),
(13, '{"en": "Rent, Arnona & Vaad Bayit", "ru": "Аренда, Арнона и Ваад байт"}', 4),
(14, '{"en": "Utilities (Metered)", "ru": "Свет, Вода, Газ"}', 4),
(15, '{"en": "Home Maintenance", "ru": "Ремонт и уют"}', 4),
(16, '{"en": "Car & Fuel", "ru": "Авто и бензин"}', 5),
(17, '{"en": "Daycare & Education", "ru": "Садик и учеба"}', 6),
(18, '{"en": "Toys & Clothes", "ru": "Игрушки и одежда"}', 6),
(19, '{"en": "Health & Beauty", "ru": "Здоровье и красота"}', 7),
(20, '{"en": "Entertainment", "ru": "Развлечения"}', 7),
(21, '{"en": "Clothing", "ru": "Одежда и обувь"}', 7),
(22, '{"en": "Subscriptions", "ru": "Подписки"}', 7),
(23, '{"en": "Loans & Debt", "ru": "Кредиты и долги"}', 8),
(24, '{"en": "Savings & Investments", "ru": "Сбережения и инвестиции"}', 8),
(25, '{"en": "Fees & Taxes", "ru": "Налоги и комиссии"}', 8),
(26, '{"en": "Cash Withdrawal", "ru": "Снятие наличных"}', 8),
(27, '{"en": "Travel & Vacation", "ru": "Путешествия и отдых"}', 7),
(28, '{"en": "Supermarkets & Groceries", "ru": "Продукты и супермаркеты"}', 3),
(29, '{"en": "Restaurants & Delivery", "ru": "Рестораны и доставка"}', 3),
(30, '{"en": "Public Transport & Taxi", "ru": "Общественный транспорт и такси"}', 5),
(31, '{"en": "Household & Cleaning", "ru": "Хозтовары и бытовая химия"}', 4),
(32, '{"en": "Internal Transfer", "ru": "Перевод между своими счетами"}', 2),
(33, '{"en": "Private Transfers & Payments", "ru": "Переводы и частные платежи"}', 2)
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    parent_id = EXCLUDED.parent_id;

-- Reset sequence
SELECT setval('budget.categories_id_seq', (SELECT max(id) FROM budget.categories));