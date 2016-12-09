#!/bin/bash
basedir=$(cd $(dirname $0); pwd)
uwsgi --http :5001 --wsgi-file app.py --callable app --procname-master UpyunDashboard.master --procname UpyunDashboard.worker --workers 4 --chdir $basedir -d uwsgi.log -M
