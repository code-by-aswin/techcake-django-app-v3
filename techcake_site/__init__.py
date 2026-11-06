# Use PyMySQL as the MySQLdb driver so Django can talk to MariaDB
# without needing a C compiler / mysqlclient build dependencies.
import pymysql

pymysql.install_as_MySQLdb()
