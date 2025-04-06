-- Rename tokensymbol to name in pumpfuninfo table
ALTER TABLE pumpfuninfo RENAME COLUMN tokensymbol TO name;

-- Rename snapshottime to snapshotat in pumpfunhistory table
ALTER TABLE pumpfunhistory RENAME COLUMN snapshottime TO snapshotat; 