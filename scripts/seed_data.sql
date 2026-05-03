-- Set the search path to include the custom schema
SET search_path TO budget, public;

-- 1. Insert Accounts
INSERT INTO accounts (id, name, type) VALUES 
(1, '{"en": "Debit", "ru": "Дебетовая"}', 'card'),
(2, '{"en": "Credit", "ru": "Кредитная"}', 'card'),
(3, '{"en": "Cash", "ru": "Наличные"}', 'cash')
ON CONFLICT (id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('accounts', 'id'), (SELECT MAX(id) FROM accounts));

-- 2. Insert top-level categories
INSERT INTO categories (id, name, parent_id) VALUES 
(1, '{"en": "Food", "ru": "Еда"}', NULL),
(2, '{"en": "Housing", "ru": "Жилье"}', NULL),
(3, '{"en": "Transport", "ru": "Транспорт"}', NULL),
(4, '{"en": "Kids", "ru": "Дети"}', NULL),
(5, '{"en": "Lifestyle", "ru": "Личные расходы"}', NULL),
(6, '{"en": "Financial", "ru": "Финансы"}', NULL),
(7, '{"en": "Pets", "ru": "Питомцы"}', NULL),
(8, '{"en": "Gifts & Charity", "ru": "Подарки и благотворительность"}', NULL)
ON CONFLICT (id) DO NOTHING;

-- 3. Insert subcategories linking to parents
-- Food (1)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Groceries", "ru": "Продукты"}', 1),
('{"en": "Dining Out", "ru": "Кафе и рестораны"}', 1),
('{"en": "Snacks & Fast Food", "ru": "Перекусы и Фастфуд"}', 1)
ON CONFLICT DO NOTHING;

-- Housing (2)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Rent & Mortgage", "ru": "Аренда и ипотека"}', 2),
('{"en": "Utilities", "ru": "Коммунальные платежи"}', 2),
('{"en": "Maintenance", "ru": "Ремонт и уют"}', 2)
ON CONFLICT DO NOTHING;

-- Transport (3)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Public Transport", "ru": "Общественный транспорт"}', 3),
('{"en": "Taxi", "ru": "Такси"}', 3),
('{"en": "Car & Fuel", "ru": "Авто и бензин"}', 3)
ON CONFLICT DO NOTHING;

-- Kids (4)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Daycare & Education", "ru": "Садик и учеба"}', 4),
('{"en": "Toys & Clothes", "ru": "Игрушки и одежда"}', 4)
ON CONFLICT DO NOTHING;

-- Lifestyle (5)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Health & Beauty", "ru": "Здоровье и красота"}', 5),
('{"en": "Entertainment", "ru": "Развлечения"}', 5),
('{"en": "Clothing", "ru": "Одежда и обувь"}', 5),
('{"en": "Subscriptions", "ru": "Подписки"}', 5)
ON CONFLICT DO NOTHING;

-- Financial (6)
INSERT INTO categories (name, parent_id) VALUES 
('{"en": "Loans & Debt", "ru": "Кредиты и долги"}', 6),
('{"en": "Savings & Investments", "ru": "Сбережения и инвестиции"}', 6),
('{"en": "Fees & Taxes", "ru": "Налоги и комиссии"}', 6)
ON CONFLICT DO NOTHING;

-- Synchronize the ID sequence for the categories table
SELECT setval(pg_get_serial_sequence('categories', 'id'), (SELECT MAX(id) FROM categories));

-- 4. Initial item aliases (Dictionary)
-- Mapping common words to their respective subcategories
-- Groceries = subcategory ID 9 (assuming sequential insertion after 8 top-levels, but to be safe we'll just insert names without guessing dynamic IDs in this static file. 
-- Wait, we can use subqueries to get exact IDs dynamically so it's robust!)

INSERT INTO item_aliases (name, category_id) VALUES 
('продукты', (SELECT id FROM categories WHERE name->>'en' = 'Groceries')),
('кола', (SELECT id FROM categories WHERE name->>'en' = 'Snacks & Fast Food')),
('такси', (SELECT id FROM categories WHERE name->>'en' = 'Taxi')),
('корм', (SELECT id FROM categories WHERE name->>'en' = 'Pets')),
('садик', (SELECT id FROM categories WHERE name->>'en' = 'Daycare & Education'))
ON CONFLICT DO NOTHING;

-- 5. Initial account aliases (Dictionary)
INSERT INTO account_aliases (name, account_id) VALUES 
('банк', 1),
('bank', 1),
('дебет', 1),
('debit', 1),
('чек', 1),
('check', 1),
('кредитка', 2),
('карта', 2),
('card', 2),
('кредит', 2),
('наличные', 3),
('нал', 3),
('кэш', 3),
('cash', 3)
ON CONFLICT DO NOTHING;