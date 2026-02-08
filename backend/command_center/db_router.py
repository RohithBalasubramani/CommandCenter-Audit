"""
Database Router for Command Center Multi-Database Setup

Routes queries between:
- 'default' (SQLite): Django admin, auth, RAG models, user memory, etc.
- 'timeseries' (PostgreSQL): Time-series equipment data from command_center_data DB

This allows the AI system to access 3 years of historical equipment data
while keeping the admin and application data in SQLite.
"""


class TimeSeriesRouter:
    """
    Database router that directs time-series queries to PostgreSQL.

    All models stay in the 'default' database (SQLite). Time-series data
    is accessed via direct SQL queries through the TimeSeriesDataAccess service.

    This design keeps Django migrations simple while allowing the AI system
    to query the massive historical dataset in PostgreSQL.
    """

    def db_for_read(self, model, **hints):
        """
        All Django model reads use 'default'.
        Time-series data is accessed via raw SQL, not Django ORM.
        """
        return 'default'

    def db_for_write(self, model, **hints):
        """
        All Django model writes use 'default'.
        Time-series data is read-only for the AI system.
        """
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the default database.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only migrate on 'default'. The 'timeseries' DB schema is managed
        by the rl_training_data generation scripts.
        """
        return db == 'default'
