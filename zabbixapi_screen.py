# -*- coding: utf-8 -*-
#from ansibles_2 import *
import ConfigParser
import json
import urllib2
import re
import sys
import ast
import time
import commands
import argparse



#"selectGraphs": ["graphid"] 对应的screen 的 resourcetype 的 0-graph    (20-graph prototype)
#"selectItems": ["itemid","value_type"] 对应的screen 的 resourcetype 的 1-simple graph      (19-simple graph prototype)




class ZabbixAPI:
    def __init__(self):
        self.__url = "http://192.168.1.100/api_jsonrpc.php"
        self.__user= "admin"
        self.__password = "zabbix"
        self.__header = {"Content-Type": "application/json-rpc"}
        self.__token_id = self.UserLogin()
    #登陆获取token
    def UserLogin(self):
        data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": self.__user,
                "password": self.__password
            },
            "id": 0,
        }
        return self.PostRequest(data)
    #推送请求
    def PostRequest(self, data):
        request = urllib2.Request(self.__url,json.dumps(data),self.__header)
        try:
            result = urllib2.urlopen(request)
            response = json.loads(result.read())
        except Exception as f:
            logger.debug(str(f))
            sys.exit(1)
        try:
            # print response['result']
            return response['result']
        except KeyError:
            return None
    #获取screen
    def ScreenGet(self):
        data = {
         "jsonrpc": "2.0",
         "method": "screen.get",
         "params": {
            "selectScreenItems": 'extend',       
            "output": "extend",
           },
         "auth": self.__token_id,
         "id":1,
            }
        return self.PostRequest(data)
    # 创建screen
    def ScreenCreate(self,screen_name,screenitems_list,columns):
        if len(screenitems_list) % columns == 0:
            vsize = len(screenitems_list) / columns
        else:
            vsize = len(screenitems_list) / columns + 1
        data = {
         "jsonrpc": "2.0",
         "method": "screen.create",
         "params": {
            "name": screen_name,
            "hsize": columns, # 列 
            "vsize": vsize,   # 行
            "screenitems": []
           },
         "auth": self.__token_id,
         "id":1,
            }
        for i in screenitems_list:
            data['params']['screenitems'].append(i)
        res =  self.PostRequest(data)
        if res:
            res = "***创建screen成功 id为%s" % str(res['screenids'][0])
        else:
            res = u"***创建screen失败 screen 可能已存在"
        return res 
    # 通过groupid 过滤返回主机列表
    def HostGet(self,item_name,columns,groupid=None,graphtype=1):
        if graphtype == 1:
            selectkey = "selectItems"
            selectvalue = ["itemid","value_type","name"]      
        if graphtype == 0:
            selectkey = "selectGraphs"
            selectvalue = ["name","graphid"]
        data = {
         "jsonrpc": "2.0",
         "method": "host.get",
         "params": {
            "output": ["hostid","name",'host'],
            selectkey: selectvalue,
            "searchByAny": 1,
           },
         "auth": self.__token_id,
         "id":1,
            }
        if groupid:
            data['params']['groupids'] = groupid
        #return self.PostRequest(data)
        output = self.PostRequest(data)
        graphs = []
        c = [] #统计一共多少个主机有该item_name
        if graphtype == 1:
            for x in output:
                for y in x['items']:
                    if y['name'] == item_name and int(y['value_type']) in [0,3]: # 0 float型数据 1 字符串 2 log类型 3 整数  (4 text文本不支持)
                        graphs.append(y['itemid'])
                        c.append(x)
        if graphtype == 0:
            for x in output:
                for y in x['graphs']:
                    if y['name'] == item_name:
                        graphs.append(y['graphid'])
                        c.append(x)
        if not graphs:
            print ("""***你指定的item_name在screentype类型为%s时不存在!!退出
                   \t 请用-t 指定其他类型重试 """ % graphtype )     
            sys.exit(1)
        else:
            ret = [ i for i in output if i not in c ]
            if ret:
               for x in ret:
                   print ("-----------------------------------")
                   print ("***主机%s 没有 %s"  % (str(x['name']),item_name))
                   print ("-----------------------------------")
        graph_list = []
        x = 0  #初始化列
        y = 0  #初始化行
                 
        for graph in graphs:
            graph_list.append({
                     #https://www.zabbix.com/documentation/3.2/manual/api/reference/screenitem/object
                    "resourcetype": graphtype,
                    "resourceid": graph,
                    "width": "500",  #图表的宽
                    "height": "100", #高度 
                    "x": str(x),
                    "y": str(y),
                    "colspan": "1",  #合并列
                    "rowspan": "1",  #合并行
                    "elements": "0", #显示在屏幕上的行数 默认25
                    "valign": "0",   # 指定屏幕在垂直方向上居中对齐 1 top 2 bottom
                    "halign": "0",   # 水平方向上居中对齐 1 left 2 right
                    "style": "0",
                    "url": "",
                    "dynamic": '0'   # 不启用连动

                           })
            x += 1
            if x == columns:
                x = 0
                y += 1
        return graph_list
    #返回主机组 得到主机组的groupid
    def HostGroupGet(self,groupname=None):
        data = {
            "jsonrpc":"2.0",
            "method":"hostgroup.get",
            "params":{
                "output": ['name','groupid'],
                "with_items": True, # 只返回带有主机或者模板的主机组
                "sortfield": "name",
            },
        "auth": self.__token_id,
        "id":1,
        }
        if groupname:
            data['params']["filter"] = {"name":[groupname]}
        gres = self.PostRequest(data)
        if gres:
            return gres[0]['groupid']
        else:
            print ("***您指定的groupname不存在(或者此组内没有主机和模板),忽略groupname")
            return None
    def goexec(self,screen_name,columns,groupname,item_name,screentype):
        group_id=self.HostGroupGet(groupname)
        graphs=self.HostGet(item_name,columns,group_id,screentype)
        res = self.ScreenCreate(screen_name,graphs,columns)
        print (res)

def main():
    zapi=ZabbixAPI()
    token=zapi.UserLogin()
    parser = argparse.ArgumentParser(description='Create Zabbix screen from all of a host Items or Graphs.')
    parser.add_argument('item_name', metavar="I", type=str,
                        help='指定对于创建screen的items 如“ICMP ping”')
    parser.add_argument('screenname', metavar='N', type=str,
                        help='Screens name for Zabbix')
    parser.add_argument('-c', dest='columns', type=int, default=2,
                        help='number of columns in the screen (default: 2)')
    parser.add_argument('-g', dest='groupname', type=str, default=None,
                        help='Specify a name for host groups and the groups must contain the host or template (default: None)')
    parser.add_argument('-t', dest='screentype', type=int, choices=[0,1], default=1,
                        help='select 0 ( graphs )  or 1  (default: 1, regular simple graphs or items) ')

    args = parser.parse_args()
    item_name = args.item_name
    screenname = args.screenname
    columns = args.columns
    groupname = args.groupname
    screentype = args.screentype
    print ("""##############################
                 screen名称: %s
                 screen类型为: %s 
                 item名称为: %s
                 group名为: %s
                 columns为: %s
##############################""") % (screenname,str(screentype),item_name,groupname,str(columns))
    zapi.goexec(screenname,columns,groupname,item_name,screentype)

if __name__ == '__main__':
    main()
