-- Seed categories
INSERT INTO budget.categories (id, name, parent_id) VALUES
-- Parent Categories (NULL)
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

-- Income (1)
(11, '{"en": "Salary", "ru": "Зарплата"}', 1),
(12, '{"en": "Refunds & Cashback", "ru": "Возвраты и кэшбэк"}', 1),
(13, '{"en": "Other Income", "ru": "Прочие доходы"}', 1),

-- Transfer (2)
(14, '{"en": "Internal Transfer", "ru": "Перевод между своими счетами"}', 2),
(15, '{"en": "Private Transfers & Payments", "ru": "Переводы и частные платежи"}', 2),

-- Food (3)
(16, '{"en": "Junk Food & Sweets", "ru": "Вредная еда и сладости"}', 3),
(17, '{"en": "Supermarkets & Groceries", "ru": "Продукты и супермаркеты"}', 3),
(18, '{"en": "Restaurants & Delivery", "ru": "Рестораны и доставка"}', 3),

-- Housing (4)
(19, '{"en": "Internet & Mobile", "ru": "Связь и интернет"}', 4),
(20, '{"en": "Rent, Arnona & Vaad Bayit", "ru": "Аренда, Арнона и Ваад байт"}', 4),
(21, '{"en": "Utilities (Metered)", "ru": "Свет, Вода, Газ"}', 4),
(22, '{"en": "Home Maintenance", "ru": "Ремонт и уют"}', 4),
(23, '{"en": "Household & Cleaning", "ru": "Хозтовары и бытовая химия"}', 4),

-- Transport (5)
(24, '{"en": "Car & Fuel", "ru": "Авто и бензин"}', 5),
(25, '{"en": "Public Transport & Taxi", "ru": "Общественный транспорт и такси"}', 5),
(26, '{"en": "Car Maintenance & Repairs", "ru": "Сервис и ремонт авто"}', 5),
(27, '{"en": "Car Insurance & Licensing", "ru": "Страховка и налоги на авто"}', 5),

-- Kids (6)
(28, '{"en": "Daycare & Education", "ru": "Садик и учеба"}', 6),
(29, '{"en": "Toys & Clothes", "ru": "Игрушки и одежда"}', 6),

-- Lifestyle (7)
(30, '{"en": "Health & Beauty", "ru": "Здоровье и красота"}', 7),
(31, '{"en": "Entertainment", "ru": "Развлечения"}', 7),
(32, '{"en": "Clothing", "ru": "Одежда и обувь"}', 7),
(33, '{"en": "Subscriptions", "ru": "Подписки"}', 7),
(34, '{"en": "Travel & Vacation", "ru": "Путешествия и отдых"}', 7),
(35, '{"en": "Hobbies & Sport", "ru": "Хобби и спорт"}', 7),

-- Financial (8)
(36, '{"en": "Loans & Debt", "ru": "Кредиты и долги"}', 8),
(37, '{"en": "Savings & Investments", "ru": "Сбережения и инвестиции"}', 8),
(38, '{"en": "Fees & Taxes", "ru": "Налоги и комиссии"}', 8),
(39, '{"en": "Cash Withdrawal", "ru": "Снятие наличных"}', 8),
(40, '{"en": "Unaccounted Expenses", "ru": "Неучтенные расходы"}', 8)

ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    parent_id = EXCLUDED.parent_id;

-- Reset sequence
SELECT setval('budget.categories_id_seq', (SELECT max(id) FROM budget.categories));

-- Seed default accounts
INSERT INTO budget.accounts (id, name, type, owner_id) VALUES
(1, '{"en": "Andrey", "ru": "Андрей"}', 'card', NULL),
(2, '{"en": "Katya", "ru": "Катя"}', 'card', NULL),
(3, '{"en": "Family", "ru": "Семья"}', 'card', NULL),
(4, '{"en": "Shared Cash", "ru": "Общий сейф"}', 'cash', NULL),
(5, '{"en": "Transit (Bit/Paybox)", "ru": "Транзит (Bit/Paybox)"}', 'transit', NULL)
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    owner_id = EXCLUDED.owner_id;

-- Reset sequence for accounts
SELECT setval('budget.accounts_id_seq', (SELECT max(id) FROM budget.accounts));

-- Seed account aliases
INSERT INTO budget.account_aliases (name, account_id) VALUES
('4787', 1),
('6747', 2),
('5883', 3),
('fibisave', 3),
('нал', 4),
('наличные', 4),
('кэш', 4),
('cash', 4)
ON CONFLICT (name) DO UPDATE SET
    account_id = EXCLUDED.account_id;