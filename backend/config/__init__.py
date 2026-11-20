"""Project package.

PyMySQL is used as a pure-python MySQL driver so the project installs
without a C compiler on Windows. It reports a mysqlclient-compatible
version, which Django checks at startup.
"""
import pymysql

pymysql.install_as_MySQLdb()
