
===
# python zabbixapi_screen.py -h
usage: zabbixapi_screen.py [-h] [-c COLUMNS] [-g GROUPNAME] [-t {0,1}] I N

Create Zabbix screen from all of a host Items or Graphs.

positional arguments:
  I             指定对于创建screen的items 如“ICMP ping”
  N             Screens name for Zabbix

optional arguments:
  -h, --help    show this help message and exit
  -c COLUMNS    number of columns in the screen (default: 2)
  -g GROUPNAME  Specify a name for host groups and the groups must contain the
                host or template (default: None)
  -t {0,1}      select 0 ( graphs ) or 1 (default: 1, regular simple graphs or
                items)
===
