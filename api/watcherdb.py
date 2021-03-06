# Copyright (c) 2017 by Telcoware
# All Rights Reserved.
# SONA Monitoring Solutions.

import sys
import sqlite3

from sona_log import LOG
from config import CONF


class DB(object):
    NODE_INFO_TBL = 't_nodes'
    REGI_SYS_TBL = 't_regi'
    EVENT_TBL = 't_event'
    STATUS_TBL = 't_status'
    RESOURCE_TBL = 't_resource'

    def __init__(self):
        self._conn = self.connection()
        self._conn.commit()

    @staticmethod
    def connection():
        try:
            conn = sqlite3.connect(CONF.base()['db_file'])
            conn.isolation_level = None
            return conn
        except:
            LOG.exception()
            sys.exit(1)

    @classmethod
    def db_cursor(cls):
        return cls.connection().cursor()

    # init DB table
    # make to empty table by default
    @classmethod
    def db_initiation(cls):
        LOG.info("--- Initiating SONA DB ---")
        init_sql = ['CREATE TABLE ' + cls.NODE_INFO_TBL +
                        '(nodename text primary key, ip_addr, username)',
                    'CREATE TABLE ' + cls.STATUS_TBL +
                    '(nodename text primary key, ping, app, cpu, memory, disk, time)',
                    'CREATE TABLE ' + cls.RESOURCE_TBL + '(nodename text primary key, cpu real, memory real, disk real)',
                    'CREATE TABLE ' + cls.REGI_SYS_TBL + '(url text primary key, auth)',
                    'CREATE TABLE ' + cls.EVENT_TBL + '(nodename, item, grade, desc, time, PRIMARY KEY (nodename, item))']

        for sql in init_sql:
            sql_rt = cls.sql_execute(sql)

            if "already exist" in sql_rt:
                table_name = sql_rt.split()[1]
                LOG.info("\'%s\' table already exist. Delete all tuple of this table...",
                         table_name)
                sql = 'DELETE FROM ' + table_name
                sql_rt = cls.sql_execute(sql)
                if sql_rt != 'SUCCESS':
                    LOG.info("DB %s table initiation fail\n%s", table_name, sql_rt)
                    sys.exit(1)
            elif sql_rt != 'SUCCESS':
                LOG.info("DB initiation fail\n%s", sql_rt)
                sys.exit(1)

        LOG.info('Insert nodes information ...')
        for node in CONF.watchdog()['check_system']:
            if str(node).lower() == 'onos':
                cls.sql_insert_nodes(CONF.onos()['list'],
                                     str(CONF.onos()['account']).split(':')[0])
            elif str(node).lower() == 'xos':
                cls.sql_insert_nodes(CONF.xos()['list'],
                                     str(CONF.xos()['account']).split(':')[0])
            elif str(node).lower() == 'swarm':
                cls.sql_insert_nodes(CONF.swarm()['list'],
                                     str(CONF.swarm()['account']).split(':')[0])
            elif str(node).lower() == 'openstack':
                cls.sql_insert_nodes(CONF.openstack()['list'],
                                     str(CONF.openstack()['account']).split(':')[0])


    @classmethod
    def sql_insert_nodes(cls, node_list, username):

        for node in node_list:
            name, ip = str(node).split(':')
            LOG.info('Insert node [%s %s %s]', name, ip, username)
            sql = 'INSERT INTO ' + cls.NODE_INFO_TBL + \
                  ' VALUES (\'' + name + '\',\'' + ip + '\',\'' + username + '\')'
            LOG.info('%s', sql)
            sql_rt = cls.sql_execute(sql)
            if sql_rt != 'SUCCESS':
                LOG.info(" [NODE TABLE] Node data insert fail \n%s", sql_rt)
                sys.exit(1)

            # set status tbl
            sql = 'INSERT INTO ' + cls.STATUS_TBL + \
                  ' VALUES (\'' + name + '\', \'none\', \'none\', \'none\', \'none\', \'none\', \'none\')'
            LOG.info('%s', sql)
            sql_rt = cls.sql_execute(sql)
            if sql_rt != 'SUCCESS':
                LOG.info(" [STATUS TABLE] Node data insert fail \n%s", sql_rt)
                sys.exit(1)

            # set resource tbl
            sql = 'INSERT INTO ' + cls.RESOURCE_TBL + ' VALUES (\'' + name + '\', -1, -1, -1)'
            LOG.info('%s', sql)
            sql_rt = cls.sql_execute(sql)
            if sql_rt != 'SUCCESS':
                LOG.info(" [RESOURCE TABLE] Node data insert fail \n%s", sql_rt)
                sys.exit(1)

            # add Alarm Items
            for item in CONF.alarm()['item_list']:
                LOG.info('Insert item [%s %s]', name, item)
                sql = 'INSERT INTO ' + cls.EVENT_TBL + \
                      ' VALUES (\'' + name + '\',\'' + item + '\',\'none\', \'none\', \'none\')'
                LOG.info('%s', sql)
                sql_rt = cls.sql_execute(sql)
                if sql_rt != 'SUCCESS':
                    LOG.info(" [ITEM TABLE] Item data insert fail \n%s", sql_rt)
                    sys.exit(1)

    @classmethod
    def sql_execute(cls, sql, conn = None):
        try:
            if conn == None:
                with cls.connection() as conn:
                    conn.cursor().execute(sql)
                    conn.commit()

                conn.close()
            else:
                conn.cursor().execute(sql)
                conn.commit()

            return 'SUCCESS'
        except sqlite3.OperationalError, err:
            LOG.error(err.message)
            return err.message
        except:
            LOG.exception()
            return 'FAIL'


DB_CONN = DB().connection()
