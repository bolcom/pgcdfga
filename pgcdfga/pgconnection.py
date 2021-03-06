#!/usr/bin/env python

# Copyright 2019 Bol.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
Module that connects to postgres and can manage resources, like databases, roles and grants.

=== Authors
Sebastiaan Mannem <smannem@bol.com>
Jing Rao <jrao@bol.com>
'''

import os
from copy import copy
import logging
import hashlib
import tempfile
import psycopg2
from psycopg2 import sql

VALID_ROLE_OPTIONS = {'SUPERUSER': 'rolsuper',
                      'NOSUPERUSER': 'not rolsuper',
                      'NOCREATEDB': 'not rolcreatedb',
                      'CREATEROLE ': 'rolcreaterole',
                      'NOCREATEROLE': 'not rolcreaterole',
                      'CREATEUSER ': 'rolcreaterole',
                      'NOCREATEUSER': 'not rolcreaterole',
                      'INHERIT ': 'rolinherit',
                      'NOINHERIT': 'not rolinherit',
                      'LOGIN': 'rolcanlogin',
                      'NOLOGIN': 'not rolcanlogin',
                      'REPLICATION': 'rolreplication',
                      'NOREPLICATION': 'not rolreplication'}

PROTECTED_ROLES = ['aq_administrator_role', 'enterprisedb', 'postgres',
                   'pg_monitor', 'pg_read_all_settings', 'pg_read_all_stats',
                   'pg_stat_scan_tables', 'pg_signal_backend',
                   'pg_read_server_files', 'pg_write_server_files',
                   'pg_execute_server_program', 'pg_signal_backend']

PROTECTED_DBS = ['postgres', 'template0', 'template1']

DB_DEFAULTS = {'owner': None, 'ensure': 'present', 'extensions': {}}

EXTENSION_DEFAULTS = {'schema': 'public',
                      'version': None,
                      'ensure': 'present'}

ROLE_DEFAULTS = {'ensure': 'present',
                 'memberof': [],
                 'options': []}

USER_DEFAULTS = {'ensure': 'present',
                 'auth': 'password',
                 'expiry': None,
                 'memberof': [],
                 'password': None,
                 'options': []}

STRICT_DEFAULTS = {'users': True, 'databases': False, 'extensions': True}


class PGConnectionException(Exception):
    '''
    This exception is raised when invalid data is fed to a PGConnectionException
    '''


# pylint: disable=R0904
class PGConnection():
    '''
    This class is used to connect to a postgres cluster and to run logical functionality
    through methods of this class, like dropdb, createdb, etc.
    '''
    def __init__(self, dsn_params=None, strict_params=copy(STRICT_DEFAULTS)):
        '''
        Sets some defaults on a new initted PGConnection class.
        '''
        if not isinstance(dsn_params, dict) or not dsn_params:
            raise PGConnectionException('Init PGConnection class with a dict of connection \
                                         parameters')
        self.__dsn_params = dsn_params
        self.__conn = {}
        self.__rolegrants = {}
        self.__databases = set()
        self.__extensions = {}
        self.strict_params = strict_params

    def dsn(self, dsn_params=None):
        '''
        This method returns the DSN that is used for the current connection.
        '''
        if not dsn_params:
            dsn_params = copy(self.__dsn_params)
            for key in ['password', 'dbname']:
                try:
                    del dsn_params[key]
                except KeyError:
                    pass
        for key in ['sslkey', 'sslcert', 'sslrootcert']:
            if key in dsn_params:
                dsn_params[key] = os.path.realpath(os.path.expanduser(dsn_params[key]))
        return " ".join(["=".join((k, str(v))) for k, v in dsn_params.items()])

    def strict_option(self, chapter=''):
        '''
        This method returns the strict config setting, which can enable / disable removing objects.
        '''
        try:
            return self.strict_params[chapter]
        except KeyError:
            return STRICT_DEFAULTS[chapter]

    def connect(self, database: str = 'postgres'):
        '''
        Connect to a pg cluster. You can specify the connectstring, or use the one
        thats already set during init, or a previous connect.
        If a succesful connection is already there, connect will be skipped.
        '''
        try:
            if not self.__conn[database].closed:
                return
        except (KeyError, AttributeError):
            pass
        # Split 'host=127.0.0.1 dbname=postgres' in {'host': '127.0.0.1', 'dbname': 'postgres'}
        dsn_params = copy(self.__dsn_params)
        dsn_params['dbname'] = database

        # Work around. Secrets don't get proper permissions when uid!=0.
        # That breaks client authentication. Therefore copying fle contents to a new file
        # (in RAM) with proper permissions so that at least client auth works.
        # And cleaning it up when connection is made
        newkeyfile = None
        if 'sslkey' in dsn_params:
            try:
                dsn_params['sslkey'] = newkeyfile = set_correct_permissions(dsn_params['sslkey'])
            except (OSError, FileNotFoundError) as error:
                logging.debug('Could not set proper permissions for key file %s.\n'
                              'Trying without sslkey in connectstring.',
                              dsn_params['sslkey'])
                logging.exception(str(error))

            if newkeyfile:
                dsn_params['sslkey'] = newkeyfile
            else:
                del dsn_params['sslkey']

        # Join {'host': '127.0.0.1', 'dbname': 'postgres'} into 'host=127.0.0.1 dbname=postgres'
        dsn = self.dsn(dsn_params)

        self.__conn[database] = conn = psycopg2.connect(dsn)
        conn.autocommit = True
        if newkeyfile:
            clean_key_file(newkeyfile)

    def run_sql(self, query, parameters=None, database: str = 'postgres'):
        '''
        Run a query. If the query returns results, the results are returned by this function
        as a list of dictionaries, e.a.:
          [{'name': 'postgres', 'oid': 12345}, {'name': 'template1', 'oid': 12346}]).
        '''
        self.connect(database=database)
        cur = self.__conn[database].cursor()
        try:
            logging.debug('query: %s', query)
            cur.execute(query, parameters)
        except Exception as error:
            logging.exception(str(error))
            raise
        try:
            columns = [i[0] for i in cur.description]
        except TypeError:
            return None
        ret = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        return ret

    def is_standby(self):
        '''
        This simple helper function detects if this instance is an standby.
        '''
        result = self.run_sql('SELECT pg_is_in_recovery() AS recovery')
        return result[0]['recovery']

    def dropdb(self, dbname):
        '''
        This method will remove a database if it exists.
        '''
        if not self.strict_option('databases'):
            logging.info('Not dropping database %s (config/strict/databases is not True)', dbname)
            return False

        if self.run_sql('SELECT datname FROM pg_database WHERE datname = %s', [dbname]):
            query = sql.SQL("DROP DATABASE {}").format(sql.Identifier(dbname))
            self.run_sql(query)
            logging.info("Dropped database '%s'", dbname)
            return True
        return False

    def createdb(self, dbname, ownername=None):
        '''
        This method will create a database if it does not exist.
        '''
        ret = False
        if not ownername:
            ownername = dbname
        readonlyrolename = '{}_readonly'.format(dbname)
        database = sql.Identifier(dbname)
        owner = sql.Identifier(ownername)
        readonlyrole = sql.Identifier(readonlyrolename)
        self.__databases.add(dbname)
        if self.createrole(ownername):
            ret = True
        if not self.run_sql('SELECT datname FROM pg_database WHERE datname = %s', [dbname]):
            createquery = sql.SQL("CREATE DATABASE {}").format(database)
            self.run_sql(createquery)
            logging.info("Created database '%s'", dbname)
            ret = True

        if not self.run_sql('SELECT datname FROM pg_database db inner join pg_roles rol \
                             on db.datdba = rol.oid WHERE datname = %s and \
                             rolname = %s', [dbname, ownername]):
            alterquery = sql.SQL("ALTER DATABASE {} OWNER TO {}").format(database, owner)
            self.run_sql(alterquery)
            logging.info("Altered database owner on '%s' to '%s'", dbname, ownername)
            ret = True
        # opex role has full permissions on every user database
        if self.grantrole('opex', ownername):
            ret = True
        if self.grantrole('readonly', readonlyrolename):
            ret = True

        ungranted_schemas_query = "select distinct schemaname from pg_tables \
            where schemaname not in ('pg_catalog','information_schema') \
            and schemaname||'.'||tablename not in (SELECT table_schema||'.'||table_name \
                FROM information_schema.role_table_grants \
                WHERE grantee = %s \
                and privilege_type = 'SELECT')"

        for schemaname in self.run_sql(ungranted_schemas_query, [readonlyrolename],
                                       database=dbname):
            schema = sql.Identifier(schemaname['schemaname'])
            grant_query = sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}")
            grant_query = grant_query.format(schema, readonlyrole)
            logging.debug(grant_query)
            self.run_sql(grant_query, database=dbname)
        return ret

    def droprole(self, rolename):
        '''
        This method will remove a user / role if it exists.
        '''
        if not self.strict_option('users'):
            logging.info('Not dropping user/role %s (config/strict/roless is not True)', rolename)
            return False

        if self.run_sql('SELECT rolname FROM pg_roles WHERE rolname = %s \
                         AND rolname != CURRENT_USER', [rolename]):
            role = sql.Identifier(rolename)
            db_query = "select db.datname, o.rolname as owner from pg_database db inner join \
                        pg_roles o on db.datdba = o.oid where db.datname != 'template0'"
            databases = [(db['datname'], db['owner']) for db in self.run_sql(db_query)]
            for database, ownername in databases:
                new_owner = sql.Identifier(ownername)
                reassign_query = sql.SQL("REASSIGN OWNED BY {} TO {}").format(role, new_owner)
                self.run_sql(query=reassign_query, database=database)
            drop_query = sql.SQL("DROP ROLE {}").format(role)
            self.run_sql(drop_query)
            logging.info("Dropped role '%s'", rolename)
            return True
        return False

    def createrole(self, rolename, options=None):
        '''
        This method will create a role if it does not exist.
        '''
        if rolename not in self.__rolegrants:
            self.__rolegrants[rolename] = set()

        ret = False
        role = sql.Identifier(rolename)
        if not self.run_sql('SELECT rolname FROM pg_roles WHERE rolname = %s', [rolename]):
            query = sql.SQL("CREATE ROLE {}").format(role)
            self.run_sql(query)
            logging.info("Created role '%s'", rolename)
            ret = True
        if not isinstance(options, list):
            options = []
        options = {option.upper() for option in options}
        valid_role_options_set = set(VALID_ROLE_OPTIONS.keys())
        for option in options & valid_role_options_set:
            logging.debug('createrole %s %s', rolename, option)
            option_check_query = sql.SQL('SELECT rolname FROM pg_roles \
                                          WHERE rolname = %s \
                                          AND ' + VALID_ROLE_OPTIONS[option])
            if not self.run_sql(option_check_query, [rolename]):
                logging.debug('createrole ALTER %s %s', rolename, option)
                option_set_query = sql.SQL('ALTER ROLE {} WITH ' + option).format(role)
                self.run_sql(option_set_query)
                ret = True
        if options - valid_role_options_set:
            raise PGConnectionException('Creating roles with invalid role options',
                                        rolename, options - valid_role_options_set)
        return ret

    def setpassword(self, username, password):
        '''
        This method changes the password of a user.
        It encrypts using md5, so that the cleartext password doe not end up in the log.
        Of coarse, there are a lot of more secure solutions, like ldap and client certificates.
        But for setting a password, this is the best solution, currently provided.
        '''

        user = sql.Identifier(username)

        if len(password) == 35 and password[:3] == 'md5':
            hashed_password = password
        else:
            md5 = hashlib.md5()
            md5.update((password + username).encode())
            hashed_password = 'md5' + md5.hexdigest()
        if self.run_sql('SELECT usename FROM pg_shadow WHERE usename = %s \
                         AND COALESCE(passwd, %s) != %s', [username, '', hashed_password]):
            query = sql.SQL('alter user {} with encrypted password %s').format(user)
            self.run_sql(query, [hashed_password])
            return True
        return False

    def resetpassword(self, username):
        '''
        This method resets the password of a user.
        '''

        user = sql.Identifier(username)

        if self.run_sql('SELECT usename FROM pg_shadow WHERE usename = %s AND \
                         passwd IS NOT NULL AND usename != CURRENT_USER', [username]):
            query = sql.SQL('alter user {} with password NULL').format(user)
            self.run_sql(query)
            return True
        return False

    def grantrole(self, username, rolename):
        '''
        This method will grant a role to a user.
        '''
        ret = False
        for role_tobe_created in [rolename, username]:
            if self.createrole(role_tobe_created):
                ret = True
        try:
            self.__rolegrants[rolename].add(username)
        except KeyError:
            self.__rolegrants[rolename] = set([username])
        if not self.run_sql("select granted.rolname granted_role, grantee.rolname \
                                 grantee_role from pg_auth_members auth inner join pg_roles \
                                 granted on auth.roleid = granted.oid inner join pg_roles \
                                 grantee on auth.member = grantee.oid where \
                                 granted.rolname = %s and grantee.rolname = %s",
                            [rolename, username]):
            user = sql.Identifier(username)
            role = sql.Identifier(rolename)
            query = sql.SQL("GRANT {} TO {}").format(role, user)
            self.run_sql(query)
            logging.info("Granted role '%s' to user '%s'", rolename, username)
            ret = True
        return ret

    def revokerole(self, username, rolename):
        '''
        This method will revoke a role from a user.
        '''
        check_query = 'SELECT rolname FROM pg_roles WHERE rolname = %s and rolname != CURRENT_USER'
        userexists = self.run_sql(check_query, [username])
        roleexists = self.run_sql(check_query, [rolename])
        if not userexists or not roleexists:
            return False
        user = sql.Identifier(username)
        role = sql.Identifier(rolename)
        query = sql.SQL("REVOKE {} FROM {}").format(role, user)
        self.run_sql(query)
        logging.info("Revoked role '%s' from '%s'", rolename, username)
        return True

    def strictifyroles(self):
        '''
        If you call this method when all role grants have been put in place,
        all grants that where not specified will be revoked.
        This limits role grants to only as specified in the underlying config.
        '''
        try:
            grantees_query = 'SELECT rolname grantee FROM pg_roles r JOIN pg_auth_members a \
                              ON r.oid=a.member WHERE a.roleid = (SELECT oid FROM \
                                 pg_roles WHERE rolname = %s)'
            revoked_or_dropped = 0
            all_managed_roles = set(PROTECTED_ROLES)

            for granted, grantees in self.__rolegrants.items():
                all_managed_roles.add(granted)
                all_managed_roles |= set(grantees)
                actual_grantees = self.run_sql(grantees_query, [granted])
                actual_grantees = {r['grantee'] for r in actual_grantees}
                overgranted = actual_grantees - grantees
                for grantee in overgranted:
                    self.revokerole(grantee, granted)
                    revoked_or_dropped += 1

            all_existing_roles = self.run_sql('SELECT rolname FROM pg_roles')
            for role in all_existing_roles:
                rolename = role['rolname']
                if rolename in all_managed_roles:
                    continue
                self.droprole(rolename)
                revoked_or_dropped += 1
        except Exception as error:
            logging.exception(str(error))

        if revoked_or_dropped:
            return True
        return False

    def strictifydatabases(self):
        '''
        If you call this method when all databases have been created,
        all databases that are not managed by this programm, will be cleaned
        This limits database to only as specified in the underlying config.
        Use with care.
        '''
        dropped = 0
        try:
            for dbrow in self.run_sql('SELECT datname FROM pg_database'):
                dbname = dbrow['datname']
                if dbname in self.__databases:
                    continue
                if dbname in PROTECTED_DBS:
                    continue
                self.dropdb(dbname)
                dropped += 1
        except Exception as error:
            logging.exception(str(error))
        if dropped:
            return True
        return False

    def strictifyextensions(self):
        '''
        If you call this method when all extensions have been created,
        all extensions that are not managed by this programm, will be cleaned
        This limits extensions to only as specified in the underlying config.
        '''
        dropped = 0
        try:
            for dbname in self.__databases:
                try:
                    managedextensions = self.__extensions[dbname]
                except KeyError:
                    managedextensions = []
                for extrow in self.run_sql('SELECT extname FROM pg_extension', database=dbname):
                    extname = extrow['extname']
                    if extname not in managedextensions:
                        self.dropextension(extname, dbname)
                        dropped += 1
        except Exception as error:
            logging.exception(str(error))
        if dropped:
            return True
        return False

    def dropextension(self, extension, database):
        '''
        This method will drop an extension from a database.
        '''
        if not self.strict_option('extensions'):
            logging.info('Not dropping extension %s (config/strict/extensions is not True)',
                         extension)
            return False

        if self.run_sql('SELECT datname FROM pg_database WHERE datname = %s', [database]):
            query = sql.SQL("DROP EXTENSION IF EXISTS {}").format(sql.Identifier(extension))
            self.run_sql(query, database=database)
            logging.info("Dropped extension '%s' from '%s'", extension, database)
            return True
        return False

    def createextension(self, extensionname, dbname: str = 'postgres',
                        schemaname=None, version=None):
        '''
        This method will drop an extension from a database.
        '''
        if version:
            version_query = 'SELECT extname FROM pg_extension \
                             WHERE extname = %s and extversion != %s'
            if self.run_sql(version_query, [extensionname, str(version)]):
                self.dropextension(extensionname, dbname)
        try:
            self.__extensions[dbname].add(extensionname)
        except KeyError:
            self.__extensions[dbname] = set([extensionname])

        if not self.run_sql('SELECT extname FROM pg_extension WHERE extname = %s',
                            [extensionname], dbname):
            extension = sql.Identifier(extensionname)
            create_query = []
            create_query.append(sql.SQL('CREATE EXTENSION IF NOT EXISTS {}').format(extension))
            if schemaname:
                schema = sql.Identifier(schemaname)
                schema_query = sql.SQL("SCHEMA {}").format(schema)
                create_query.append(schema_query)
            if version:
                create_query.append(sql.SQL('VERSION {}').format(sql.Identifier(str(version))))
            self.run_sql(sql.SQL(' ').join(create_query),
                         database=dbname)
            logging.info("Created extension '%s' on '%s'", extensionname, dbname)
            return True
        return False

    def create_replication_slot(self, slot_name):
        '''
        Create the named replication slot_name if it does not yet exist.
        '''
        if self.__replication_slot_exists(slot_name):
            logging.debug("Replication slot '%s' found. No need to create it.", slot_name)
        else:
            logging.debug("Replication slot '%s' not found. Will create it.", slot_name)
            query = sql.SQL("SELECT pg_create_physical_replication_slot({})") \
                       .format(sql.Literal(slot_name))
            if self.run_sql(query):
                logging.info("Created replication slot '%s'", slot_name)
                return True
            logging.error("Failed to create replication slot '%s'", slot_name)
        return False

    def drop_replication_slot(self, slot_name):
        '''
        Drop the named replication slot_name if it exists.
        '''
        if self.__replication_slot_exists(slot_name):
            logging.debug("Replication slot '%s' found. Will drop it.", slot_name)
            query = sql.SQL("SELECT pg_drop_replication_slot({})").format(sql.Literal(slot_name))
            if self.run_sql(query):
                logging.info("Dropped replication slot '%s'", slot_name)
                return True
            logging.error("Failed to drop replication slot '%s'", slot_name)
        else:
            logging.debug("Replication slot '%s' not found. No need to drop drop it.", slot_name)
        return False

    def replication_slots(self):
        '''
        Returns a list of the names of existing replication slots.
        '''
        query = sql.SQL("SELECT slot_name FROM pg_replication_slots")
        result = self.run_sql(query)
        if result:
            return [r['slot_name'] for r in result]

        logging.debug("Cluster has no existing replication slots.")
        return []

    def __replication_slot_exists(self, slot_name):
        '''
        Check if the named replication slot_name exists.
        '''
        query = sql.SQL("SELECT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = {})") \
                   .format(sql.Literal(slot_name))
        result = self.run_sql(query)
        if result and ('exists' in result[0]):
            return result[0]['exists']

        logging.error("Unable to determine if replication slot '%s' exists. "
                      "Assuming that it doesn't.", slot_name)
        return True


def set_correct_permissions(filename):
    '''
    Libpq requires client cert private keys to have very specific permissions (0600).
    This function will create a new file with correct permissions
    from a readable file with wrong permissions.
    '''
    keyfile = os.path.realpath(os.path.expanduser(filename))
    keyfilemode = oct(os.stat(keyfile).st_mode)[-4:]
    if keyfilemode != '0600':
        logging.info('Fixing permissions on key file %s (%s)', keyfile, keyfilemode)
        with open(keyfile, 'rb') as keyfile_hnd:
            key = keyfile_hnd.read()
        _nkf_handle, newkeyfile = tempfile.mkstemp()
        with open(newkeyfile, 'wb') as keyfile_hnd:
            keyfile_hnd.write(key)
        logging.debug('New key file %s is created with correct permissions', newkeyfile)
        return newkeyfile
    return None


def clean_key_file(filename):
    '''
    This function will clean a copied keyfile that was craeted by set_correct_permissions.
    It will first overwrite with other data (3 times) and then remove.
    '''
    keyfile = os.path.realpath(os.path.expanduser(filename))
    logging.debug('Cleaning key file %s', keyfile)
    with open(keyfile, 'rb') as keyfile_hnd:
        keylength = len(keyfile_hnd.read())
    for _run_index in range(5):
        for obfuscate in [b'\x00' * keylength, b'\xff' * keylength]:
            with open(keyfile, 'wb') as keyfile_hnd:
                keyfile_hnd.write(obfuscate)
    os.remove(keyfile)
