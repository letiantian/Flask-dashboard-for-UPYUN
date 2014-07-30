#!/usr/bin/env python
#-*- encoding:utf-8 -*-

__author__ = 'letian'


from flask import Flask, request, session, redirect, url_for, render_template, escape, Response

import upyun
import upyun2
import tool
import sys
import json

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024

app.secret_key = 'F12Zr47j\3yX R~X@H!jLwf/T'

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        bucketname = request.form['bucket'].strip()
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if tool.valid_login(bucketname, username, password):
            session['username'] = username
            session['bucket'] = bucketname
            session['password'] = password
            if app.debug:
                print '用户信息输入正确'
                print session
                print 'redirct to ', url_for('admin')
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', login_error=True)
    ## GET方法
    if 'username' not in session:
        return render_template('login.html', login_error=False)
    else:
        return redirect(url_for('admin'))


@app.route('/admin', methods=['GET'])
def admin():
    if 'username' not in session:
        if app.debug:
            print '还没登录呢'
        return redirect(url_for('index'))
    #若已经登录
    print '用户已经登录', session
    request_dir = request.args.get('dir', '')  #url中请求的参数
    request_dir = tool.beautify_path(request_dir.strip())
    print '请求查看的目录：',request_dir
    bucket = upyun2.UpYun2(session['bucket'], session['username'],
                           session['password'], timeout=10, endpoint=upyun.ED_AUTO)
    #url无dir参数，或者为'/'
    if len(request_dir) == 0 or request_dir == '/':
        if app.debug:
            print '显示根目录内容'
        request_dir = '/'
        dir_list = bucket.getlist(request_dir)
        dir_list=tool.process_dir_list(request_dir, dir_list)
        split_path = tool.split_path(request_dir)
        return render_template('admin.html', username=escape(session['username']),
                               bucketname=escape(session['bucket']), dir_list=dir_list,
                               split_path=split_path, request_dir=escape(request_dir))
    #若url有dir参数，非根目录dir
    if bucket.isdir(request_dir):
        if request_dir[-1] != '/':
            request_dir = request_dir + '/'
        dir_list = bucket.getlist(request_dir)
        dir_list=tool.process_dir_list(request_dir, dir_list)
        split_path = tool.split_path(request_dir)
        return render_template('admin.html', username=escape(session['username']),
                               bucketname=escape(session['bucket']), dir_list=dir_list,
                               split_path=split_path, request_dir=escape(request_dir))
    else:
        return render_template('admin.html', username=escape(session['username']),
                               bucketname=escape(session['bucket']), error='您请求的目录不存在')

'''
注销
'''
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

'''
显示文件内容，使用path指定文件路径，例如`?path=....`
'''
@app.route('/show', methods=['GET'])
def show():
    if 'username' not in session:
        if app.debug:
            print '还没登录呢'
        return redirect(url_for('index'))
    request_path = request.args.get('path', '')  #url中请求的参数path, GET专用
    request_path = tool.beautify_path(request_path.strip())
    bucket = upyun2.UpYun2(session['bucket'], session['username'],
                           session['password'], timeout=10, endpoint=upyun.ED_AUTO)
    if not bucket.exists(request_path):
        if app.debug:
            print '请求显示的文件不存在'
        return render_template('show.html', error_info="文件不存在" )
    if bucket.isdir(request_path):
        return redirect('/admin?dir='+request_path)
    if bucket.isfile(request_path):
        max_size = 500*1000  # B
        txt = ['txt', 'py', 'c', 'cpp', 'java', 'html', 'htm','xml']
        img = ['png', 'jpg', 'jpeg', 'gif']
        info = bucket.getinfo(request_path)
        if int(info['file-size']) > max_size:
            return render_template('show.html', error_info="文件太大，不支持访问" )
        if request_path.split('.')[-1].lower() in txt:
            content = bucket.get(request_path)
            return render_template('show.html', content = escape(content) )
        if request_path.split('.')[-1].lower() in img:
            content = bucket.get(request_path)
            return Response(content, mimetype='image/'+request_path.split('.')[-1])
            # return content
        return render_template('show.html', error_info="文件格式不支持" )

'''
删除文件或者目录，接受post数据，例如path=/tag/1.html

'''
@app.route('/delete', methods=['POST'])
def delete():
    if 'username' not in session:
        if app.debug:
            print '还没登录呢'
        return redirect(url_for('index'))
    request_path = request.form['path'].strip()  #request.form -> POST专用
    request_path = tool.beautify_path(request_path.strip())
    if app.debug:
        print '要删除的文件或者目录 ', request_path
    bucket = upyun2.UpYun2(session['bucket'], session['username'],
                           session['password'], timeout=10, endpoint=upyun.ED_AUTO)
    if not bucket.exists(request_path):
        if app.debug:
            print '文件不存在，无法删除'
        re_info = {'error':True, 'info':'要删除的文件或者目录不存在'}
        return json.dumps(re_info)
    if bucket.isfile(request_path):
        try:
            bucket.delete(request_path)
            re_info = {'error':False, 'info':''}
            return json.dumps(re_info)
        except:
            re_info = {'error':True, 'info':'删除过程中出现错误，请稍后再试'}
            return json.dumps(re_info)
    if bucket.isdir(request_path):
        try:
            bucket.remove_dir(request_path)
            re_info = {'error':False, 'info':''}
            return json.dumps(re_info)
        except:
            re_info = {'error':True, 'info':'删除过程中出现错误，请稍后再试'}
            return json.dumps(re_info)

'''
创建目录，只支持一层。
接受POST的数据，current_dir指明当前的目录（在这个目录下创建新的目录），dir_name指明要创建的目录名称
'''
@app.route('/mkdir', methods=['POST'])
def mkdir():
    if 'username' not in session:
        if app.debug:
            print '还没登录呢'
        return redirect(url_for('index'))
    current_dir = request.form['current_dir'].strip()
    dir_name = request.form['dir_name'].strip()
    bucket = upyun2.UpYun2(session['bucket'], session['username'],
                           session['password'], timeout=10, endpoint=upyun.ED_AUTO)
    if not bucket.exists(current_dir):
        re_info = {'error':True, 'info':'路径不存在，无法在其中创建目录'}
        return json.dumps(re_info)
    if '/' in dir_name:
        re_info = {'error':True, 'info':'目录名包含特殊字符，请重新填写'}
        return json.dumps(re_info)
    combine_name = tool.beautify_path(current_dir+'/'+dir_name)
    if app.debug:
        print '要创建目录: ', combine_name
    if bucket.exists(combine_name):
        re_info = {'error':True, 'info':'相同名称的目录或者文件已经存在'}
        return json.dumps(re_info)
    try:
        bucket.mkdir(combine_name)
        re_info = tool.process_folder_info(bucket.getinfo(combine_name))
        re_info['path'] = combine_name
        re_info['name'] = dir_name
        re_info['error'] = False
        re_info['info'] = '目录创建成功'
        return json.dumps(re_info)
    except Exception, e:
        print e
        re_info = {'error':True, 'info':'目录创建过程中出现错误，请稍后再试'}
        return json.dumps(re_info)

'''
上传文件，接受POST数据。
'''
@app.route('/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        if app.debug:
            print '还没登录呢'
        return redirect(url_for('index'))
    try:
        current_dir = tool.beautify_path(request.args.get('dir', ''))
        filename = request.files['file'].filename
        file_content = request.files['file'].stream.read()
        file_size = len(file_content)  # Byte
        yun_path = tool.beautify_path(current_dir + '/' + filename)

        if app.debug:
            print '上传的文件信息如下：'
            print file_content
            print file_size
            print request.files
            print request.files['file']

        bucket = upyun2.UpYun2(session['bucket'], session['username'],
                           session['password'], timeout=10, endpoint=upyun.ED_AUTO)
        if bucket.exists(yun_path):
            re_info = {'error':True, 'info':filename+ '已经存在，请为您的文件修改名称'}
            return json.dumps(re_info)
        #上传到云
        bucket.put(yun_path, file_content)
        re_info = tool.process_file_info( bucket.getinfo(yun_path) )
        re_info['path'] = yun_path
        re_info['name'] = filename
        re_info['error'] = False
        re_info['info'] = '文件'+ filename +'上传成功'
        return json.dumps(re_info)
    except:
        re_info = {'error':True, 'info':'文件'+ filename +'暂时无法上传到又拍云，请稍后再试'}
        return json.dumps(re_info)

if __name__ == '__main__':
    ## 调试模式
    app.run(debug=True)

    ## 使用80端口，并允许其他主机使用
    # app.run(host='0.0.0.0', port=80)
