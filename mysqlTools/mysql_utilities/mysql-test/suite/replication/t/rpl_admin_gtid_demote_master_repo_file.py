#
# Copyright (c) 2013, Oracle and/or its affiliates. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
#

import mutlib
import rpl_admin
from mysql.utilities.exception import MUTLibError

_DEFAULT_MYSQL_OPTS_FILE = ('"--log-bin=mysql-bin --skip-subordinate-start '
                           '--log-subordinate-updates --gtid-mode=on '
                           '--enforce-gtid-consistency '
                           '--report-host=localhost --report-port=%s '
                           '--main-info-repository=file"')


class test(rpl_admin.test):
    """test replication administration commands
    This test runs the mysqlrpladmin utility on a known topology.

    Note: this test requires GTID enabled servers.
    """

    def check_prerequisites(self):
        if not self.servers.get_server(0).check_version_compat(5, 6, 9):
            raise MUTLibError("Test requires server version 5.6.9")
        return self.check_num_servers(1)

    def setup(self):
        self.res_fname = "result.txt"

        # Spawn servers
        self.server0 = self.servers.get_server(0)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server1 = self.spawn_server("rep_main_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server2 = self.spawn_server("rep_subordinate1_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server3 = self.spawn_server("rep_subordinate2_gtid", mysqld, True)
        mysqld = _DEFAULT_MYSQL_OPTS_FILE % self.servers.view_next_port()
        self.server4 = self.spawn_server("rep_subordinate3_gtid", mysqld, True)

        self.m_port = self.server1.port
        self.s1_port = self.server2.port
        self.s2_port = self.server3.port
        self.s3_port = self.server4.port

        rpl_admin.test.reset_topology(self)

        return True

    def run(self):
        test_num = 1

        main_conn = self.build_connection_string(self.server1).strip(' ')
        subordinate1_conn = self.build_connection_string(self.server2).strip(' ')
        subordinate2_conn = self.build_connection_string(self.server3).strip(' ')
        subordinate3_conn = self.build_connection_string(self.server4).strip(' ')
        #subordinate4_conn = self.build_connection_string(self.server5).strip(' ')

        comment = ("Test case %s - mysqlrplshow OLD Main before demote"
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % main_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        comment = ("Test case %s - mysqlrplshow not yet NEW Main Before "
                   "switchover demote" 
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate1_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        # mysqlrpladmin --main=root:root@localhost:13091 
        # --new-main=root:root@localhost:13094 
        # --discover-subordinates-login=root:root --demote-main  switchover 
        # --rpl-user=rpl:rplpass 
        comment = ("Test case %s - demote-main switchover -vvv "
                   "using actual rpl user"
                   % test_num)
        subordinates = ",".join([subordinate1_conn, subordinate2_conn, subordinate3_conn])
        cmd_str = "mysqlrpladmin.py --main=%s " % main_conn
        cmd_opts = [" --new-main=%s  " % subordinate1_conn,]
        cmd_opts.append("--discover-subordinates=%s " % main_conn.split('@')[0])
        cmd_opts.append("--rpl-user=rpl:rpl ")
        cmd_opts.append("--demote-main switchover -vvv")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow OLD Main after demote"
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % main_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        comment = ("Test case %s - mysqlrplshow NEW Main" 
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate1_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        # mysqlrpladmin --main=root:root@localhost:13091 
        # --new-main=root:root@localhost:13094 
        # --discover-subordinates-login=root:root --demote-main  switchover
        # --rpl-user=rpl:rplpass 
        comment = ("Test case %s - demote-main switchover -vvv "
                   "Using a different rpl user and no --force" % test_num)
        subordinates = ",".join([subordinate1_conn, subordinate2_conn, subordinate3_conn])
        cmd_str = "mysqlrpladmin.py --main=%s " % subordinate1_conn
        cmd_opts = [" --new-main=%s  " % subordinate3_conn,]
        cmd_opts.append("--discover-subordinates=%s " % main_conn.split('@')[0])
        cmd_opts.append("--rpl-user=rpluser:hispassword ")
        cmd_opts.append("--demote-main switchover -vvv")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow still OLD Main after "
                   "failed switchover demote" 
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate1_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        comment = ("Test case %s - mysqlrplshow not yet NEW Main after "
                   "failed switchover demote" 
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate3_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        # mysqlrpladmin --main=root:root@localhost:13091 
        # --new-main=root:root@localhost:13094 
        # --discover-subordinates-login=root:root --demote-main  switchover
        # --rpl-user=rpl:rplpass 
        comment = ("Test case %s - demote-main switchover -vvv "
                   "Using a different rpl user and using the --force"
                   % test_num)
        subordinates = ",".join([subordinate1_conn, subordinate2_conn, subordinate3_conn])
        cmd_str = "mysqlrpladmin.py --main=%s " % subordinate1_conn
        cmd_opts = [" --new-main=%s  " % subordinate3_conn,]
        cmd_opts.append("--discover-subordinates=%s " % main_conn.split('@')[0])
        cmd_opts.append("--rpl-user=rpluser:hispassword ")
        cmd_opts.append("--demote-main switchover -vvv ")
        cmd_opts.append("--force")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)
        self.results.append("\n")

        test_num += 1
        comment = ("Test case %s - mysqlrplshow OLD Main after demote"
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate1_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        test_num += 1
        comment = ("Test case %s - mysqlrplshow NEW Main after demote" 
                   % test_num)
        cmd_str = "mysqlrplshow.py --main=%s " % subordinate3_conn
        #  --main=root:root@localhost:13091 --disco=root:root -r
        cmd_opts = ["--discover-subordinates=%s " % main_conn.split('@')[0]]
        cmd_opts.append("-r")
        res = self.run_test_case(0, "%s %s" % (cmd_str,"".join(cmd_opts)),
                                 comment)
        if not res:
            raise MUTLibError("%s: failed" % comment)

        # Now we return the topology to its original state for other tests
        rpl_admin.test.reset_topology(self)

        # Mask out non-deterministic data
        rpl_admin.test.do_masks(self)

        self.replace_result("# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(",
                            "# QUERY = SELECT "
                            "WAIT_UNTIL_SQL_THREAD_AFTER_GTIDS(XXXXX)\n")
        self.replace_substring("localhost", "XXXXXXXXX")

        self.remove_result_and_lines_before("WARNING: There are subordinates that "
                                            "had connection errors.")

        self.replace_result("| XXXXXXXXX  | PORT2  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT2  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "|            |             |              "
                            "|                  |               |           "
                            "|                |            "
                            "|               |\n")

        self.replace_result("| XXXXXXXXX  | PORT2  | MASTER  | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT2  | MASTER  | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "|            |             |              "
                            "|                  |               |           "
                            "|                |            "
                            "|               |\n")

        self.replace_result("| XXXXXXXXX  | PORT1  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT1  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")

        self.replace_result("| XXXXXXXXX  | PORT3  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT3  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")

        self.replace_result("| XXXXXXXXX  | PORT4  | SLAVE   | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT4  | SLAVE   | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "| Yes        | Yes         | 0            "
                            "| No               | 0             |           "
                            "| 0              |            "
                            "| 0             |\n")
        
        self.replace_result("| XXXXXXXXX  | PORT4  | MASTER  | UP     "
                            "| ON         | OK      | ",
                            "| XXXXXXXXX  | PORT4  | MASTER  | UP     "
                            "| ON         | OK      | XXXXXXXX    "
                            "| XXXXXXXX          | XXXXXXXX        "
                            "|            |             |              "
                            "|                  |               |           "
                            "|                |            "
                            "|               |\n")

        self.mask_column_result("| version", "|", 2, " XXXXXXXX ")
        self.mask_column_result("| main_log_file", "|", 2, " XXXXXXXX ")
        self.mask_column_result("| main_log_pos", "|", 2, " XXXXXXXX ")

        return True

    def get_result(self):
        return self.compare(__name__, self.results)

    def record(self):
        return self.save_result_file(__name__, self.results)

    def cleanup(self):
        return rpl_admin.test.cleanup(self)

