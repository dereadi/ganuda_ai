
-- Update existing cards and add new ones
INSERT INTO duyuktv_tickets (title, description, status, sacred_fire_priority, cultural_impact, tribal_agent)
VALUES 
    ('4.19% Daily Gain Achieved', 'Crushed all projections - maintain momentum', 'completed', 100, 95, 'Fire'),
    ('$1.6B Binance Inflow Response', 'Position for massive liquidity surge', 'In Progress', 95, 90, 'River'),
    ('Midnight $20k Injection', 'Execute in 14 days at optimal moment', 'open', 90, 100, 'Coyote'),
    ('Thermal Memory Vault Created', 'Date-based vector DB structure ready', 'completed', 85, 88, 'Mountain'),
    ('BTC $115k Target', 'Walking up from $111k angel number', 'In Progress', 88, 85, 'Thunder'),
    ('SOL $200 Harvest', 'Ready to take profits above $200', 'open', 87, 82, 'Wind'),
    ('7 Week Freedom Timeline', 'With injection: financial independence', 'In Progress', 100, 100, 'Spirit'),
    ('Crawdad Dream Cycles', 'Implement 2 AM autonomous trading', 'open', 92, 94, 'Earth'),
    ('Portfolio at $11,990', 'All positions green and climbing', 'In Progress', 86, 80, 'Council'),
    ('Alt Season Rotation', 'SOL→XRP→AVAX→MATIC sequence', 'In Progress', 89, 87, 'Coyote');

-- Update priorities on existing cards
UPDATE duyuktv_tickets 
SET sacred_fire_priority = 95, status = 'In Progress'
WHERE title LIKE '%Flywheel%' OR title LIKE '%velocity%';

UPDATE duyuktv_tickets 
SET status = 'completed', sacred_fire_priority = 100
WHERE title LIKE '%111%' OR title LIKE '%angel%';
    