from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# 1. Ignorar la comprobación de versión de MariaDB
DatabaseWrapper.check_database_version_supported = lambda self: None

# 2. Desactivar 'RETURNING' para que MariaDB 10.4 no dé error de sintaxis
DatabaseFeatures.can_return_columns_from_insert = property(lambda self: False)
DatabaseFeatures.can_return_rows_from_bulk_insert = property(lambda self: False)