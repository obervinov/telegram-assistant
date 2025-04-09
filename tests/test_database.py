# """
# This module contains tests for the database module.
# """
# import os
# import sys
# import json
# import importlib
# from datetime import datetime, timedelta
# import pytest
# import psycopg2
# from psycopg2 import pool
# from src.modules.tools import get_hash
# from src.modules.database import DatabaseClient


# # pylint: disable=too-many-locals
# @pytest.mark.order(2)
# def test_init_database_client(vault_configuration_data, postgres_instance, database_class):
#     """
#     Checking an initialized database client
#     """
#     _ = vault_configuration_data
#     _, cursor = postgres_instance

#     # Check general attributes
#     assert isinstance(database_class.vault, object)
#     assert isinstance(database_class.db_role, str)
#     assert isinstance(database_class.database_connections, pool.SimpleConnectionPool)

#     # Check tables creation in the database
#     cursor.execute("SELECT * FROM information_schema.tables WHERE table_schema = 'public'")
#     tables_list = cursor.fetchall()
#     tables_configuration_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../src/configs/databases.json'))
#     with open(tables_configuration_path, encoding='UTF-8') as config_file:
#         database_init_configuration = json.load(config_file)
#     for table in database_init_configuration.get('Tables', None):
#         if table['name'] not in [table[2] for table in tables_list]:
#             assert False

#     # Check migrations execution in the database
#     cursor.execute("SELECT name, version FROM migrations")
#     migrations_list = cursor.fetchall()
#     assert len(migrations_list) > 0

#     migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/migrations'))
#     sys.path.append(migrations_dir)
#     migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
#     migration_files.sort()
#     for migration_file in migration_files:
#         if not migration_file.endswith('.py'):
#             assert False
#         else:
#             migration_module_name = migration_file[:-3]
#             migration_module = importlib.import_module(name=migration_module_name)
#             version = getattr(migration_module, 'VERSION', migration_module_name)
#             name = getattr(migration_module, 'NAME', migration_module_name)
#             if (name, version) not in migrations_list:
#                 print(f"Not found migration {name}:{version} in {migrations_list}")
#                 assert False


# @pytest.mark.order(4)
# def test_database_connection(postgres_instance, database_class):
#     """
#     Checking the database connection
#     """
#     _ = postgres_instance
#     connection = database_class.get_connection()
#     assert isinstance(connection, psycopg2.extensions.connection)
#     assert not connection.closed
#     database_class.close_connection(connection)


# @pytest.mark.order(12)
# def test_service_messages(database_class):
#     """
#     Checking the registration of service messages
#     """
#     data = {
#         'message_id': 'test_case_12',
#         'chat_id': 'test_case_12',
#         'message_content': 'Test case 12',
#         'message_type': 'status_message',
#         'state': 'updated'
#     }

#     # Keep new status_message
#     status = database_class.keep_message(**data)
#     assert status == f"{data['message_id']} kept"
#     new_message = database_class.get_considered_message(message_type=data['message_type'], chat_id=data['chat_id'])
#     assert new_message[0] == data['message_id']
#     assert new_message[1] == data['chat_id']
#     assert new_message[4] == get_hash(data['message_content'])
#     assert new_message[5] == 'added'

#     # Update exist message
#     data['message_content'] = 'Updated message'
#     status = database_class.keep_message(**data)
#     assert status == f"{data['message_id']} updated"
#     updated_message = database_class.get_considered_message(message_type=data['message_type'], chat_id=data['chat_id'])
#     assert updated_message[0] == data['message_id']
#     assert updated_message[1] == data['chat_id']
#     assert updated_message[2] != updated_message[3]
#     assert updated_message[3] != new_message[3]
#     assert updated_message[4] == get_hash(data['message_content'])
#     assert updated_message[5] == 'updated'

#     # Recreate exist message
#     data['message_content'] = 'Recreated message'
#     status = database_class.keep_message(**data, recreated=True)
#     assert status == f"{data['message_id']} recreated"
#     recreated_message = database_class.get_considered_message(message_type=data['message_type'], chat_id=data['chat_id'])
#     assert recreated_message[0] == data['message_id']
#     assert recreated_message[1] == data['chat_id']
#     assert recreated_message[2] == recreated_message[3]
#     assert recreated_message[2] != updated_message[2]
#     assert recreated_message[3] != updated_message[3]
#     assert recreated_message[4] == get_hash(data['message_content'])
#     assert recreated_message[5] == 'updated'
