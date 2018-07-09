pysmoke
=======
This script will ping list IP address & push RTA, %Loss to Influx. This repo has 2 branch, branch supervisor will run script by supervisor. After push data to influx, you can use grafana to monioring by graphs.  
Branch Master
======
Branch master run script normaly, you can use it with scheduler like crontab,... This script can use both Linux & Windows.  
Clone the repo
```
git clone https://github.com/congnt1705/Python-Monitor-Ping-And-Push-To-Influx.git
cd Python-Monitor-Ping-And-Push-To-Influx
```
You need a file config name `pysmoke.conf` like this, you can add more IP after section default ipList:
```
[default]
ipList = 1.1.1.1, 8.8.8.8, [more IP]

[influx_db]
Host = 10.5.9.204
Port = 8086
Database = pysmoke
User = root
Pass = root
```
Install env & run script
```
pipenv install
pipenv run python pysmoke.py
```

Branch supervisor
======
This branch will run script by supervisor, use only with Linux.  
Config supervisor `/etc/supervisor/conf.d/pysmoke.conf`(Ubuntu) hoặc `/etc/supervisord.d/pysmoke.ini`(CentOS)
```
[program:pysmoke]
command=pipenv run python pysmoke.py
# Change directory
directory=/root/pysmoke/
autostart=true
autorestart=true
user=root
stderr_logfile=/var/log/supervisor/pysmoke.err.log
stdout_logfile=/var/log/supervisor/pysmoke.out.log
```
Run process with supervisor
```
supervisorctl reload
```
