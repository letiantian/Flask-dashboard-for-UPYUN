#-*- encoding:utf-8 -*-

__author__ = 'letian'

import upyun
import upyun2
import time
import re

def valid_login(bucket, username, password):
    '''
    判断试图登录的用户信息是否存在
    '''
    try:
        bucket = upyun2.UpYun2(bucket, username, password, timeout=10, endpoint=upyun.ED_AUTO)
        bucket.getinfo('/') #若无法获取信息，则可能是用户信息错误
        return True
    except:
        return False

def beautify_path(path):
    '''
    ///tag///  ->/tag/
    '''
    return re.sub(r'/+', '/', path)

def process_dir_list(request_dir, dir_list):
    '''
    {name, time, type, size}
    添加path,修改time(正常表示)，大小改为KB
    '''
    count = 0
    for item in dir_list:
        item['path'] = (request_dir + '/' + item['name']).replace('//','/')
        item['time'] = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(float(item['time'])))
        item['size'] = '%.2fkB' % (float(item['size'])/1000)
        item['id'] = str(count)
        count += 1
    return dir_list

def process_folder_info(info):
    '''
    res = up.getinfo('/upyun-python-sdk/xinu.png')
    print res['file-type']  ->type:F
    print res['file-size']  ->size:*kB  ##目录没有该键
    print res['file-date']  ->time
    '''
    info2 = {}
    info2['type'] = 'F'
    info2['size'] = '0.00kB'
    info2['time'] = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(float(info['file-date'])))
    return info2

def process_file_info(info):
    '''
    res = up.getinfo('/upyun-python-sdk/xinu.png')
    print res['file-type']  ->type:F
    print res['file-size']  ->size:*kB
    print res['file-date']  ->time
    '''
    info2 = {}
    info2['type'] = 'F'
    info2['size'] = '%.2fkB' % (float(info['file-size'])/1000)
    info2['time'] = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(float(info['file-date'])))
    return info2

def split_path(path):
    '''
    /aa/sss/b  ->[{'name':'根目录',path:'/'}, {'name':'aa', 'path':'/aa'}, {'name':'sss', path:'/aa/sss'}, {'name':'b', path:'/aa/sss/b'}]
    '''
    print 'split path ', path
    path = path.decode('utf-8').strip().replace('//','/').replace('///','/')
    path_list = [{'name':'根目录', 'path':'/'}]
    if path == '/':
        return path_list
    if path[-1] == '/':
        path = path[:-1]
    sp = path.split('/')
    # for x in xrange(len(sp)):
    #     path_list.append({'name':sp[x+1], 'path':'/'.join(sp[0:x+2])})

    start = 2
    while start <= len(sp):
        path_list.append({'name':sp[start-1], 'path':'/'.join(sp[0:start])})
        start += 1

    return path_list



