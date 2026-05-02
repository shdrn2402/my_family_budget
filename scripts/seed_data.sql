-- scripts/seed_data.sql

-- Set the search path to include the custom schema
SET search_path TO budget, public;

-- 1. Insert top-level categories
INSERT INTO categories (id, name, parent_id) VALUES 
(1, 'Kids', NULL),
(2, 'Lifestyle', NULL),
(3, 'Transport', NULL),
(4, 'Financial', NULL),
(5, 'Home & Bills', NULL)
ON CONFLICT (id) DO NOTHING;

-- Synchronize the ID sequence for the categories table after explicit ID inserts
SELECT setval(pg_get_serial_sequence('categories', 'id'), (SELECT MAX(id) FROM categories));

-- 2. Insert subcategories linking to parents[cite: 2]
-- Kids (Parent: Kids)
INSERT INTO categories (name, parent_id) VALUES ('Daycare', 1) ON CONFLICT DO NOTHING;

-- Lifestyle (Parent: Lifestyle)
INSERT INTO categories (name, parent_id) VALUES 
('Health and Beauty', 2),
('Leisure and entertainment', 2)
ON CONFLICT DO NOTHING;

-- Transport (Parent: Transport)
INSERT INTO categories (name, parent_id) VALUES 
('Car', 3),
('Taxi', 3),
('Public Transport', 3)
ON CONFLICT DO NOTHING;

-- Financial (Parent: Financial)
INSERT INTO categories (name, parent_id) VALUES 
('Loans', 4),
('Subscriptions', 4)
ON CONFLICT DO NOTHING;

-- Home & Bills (Parent: Home & Bills)
INSERT INTO categories (name, parent_id) VALUES 
('Housing', 5),
('Utilities', 5),
('Telecoms', 5)
ON CONFLICT DO NOTHING;