-- Auto stop backup configure
-- This is third party add-ons 'auto_database_backup', may have issue when enable before 'auto_database_backup' is enable
UPDATE db_backup_configure
   SET active = false
 WHERE active = true;