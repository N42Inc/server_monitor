#!/bin/sh
### BEGIN INIT INFO
# Provides:          n42agent
# Required-Start:    $local_fs $network $named $time $syslog
# Required-Stop:     $local_fs $network $named $time $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       n42agent
### END INIT INFO

#Follow standards https://wiki.debian.org/LSBInitScripts

SCRIPT="stdbuf -oL nohup python /opt/agents/monitor/Agent.py"
#RUNAS=<USERNAME>

NAME="monitoragent"
PIDFILE="/var/run/$NAME.pid"
LOGFILE="/var/log/$NAME.log"

start() {
  if [ -f "$PIDFILE" ] && (ps -p $(cat "$PIDFILE") > /dev/null);
  then
     echo 'Service already running' >&2
     return 1
  fi
  echo 'Starting service…' >&2
  #https://gist.github.com/naholyr/4275302
  local CMD="$SCRIPT >> \"$LOGFILE\" 2>&1 & echo \$! > \"$PIDFILE\""
  sudo sh -c "$CMD"	
  echo 'Service started' >&2
}

stop() {
  if [ -f "$PIDFILE" ] && (ps -p $(cat "$PIDFILE") > /dev/null);
  then
    kill -0 $(cat "$PIDFILE") 2> /dev/null
    #if [ $? -ne 0 ];
    #then
    #   echo "Please run as sudo."
    #   echo "sudo service n42agent stop"
    #   return 1
    #fi
    echo 'Stopping service…' >&2
    sudo kill -15 $(cat "$PIDFILE") && sudo rm -f "$PIDFILE"
    echo 'Service stopped' >&2
  else
    echo 'Service not running' >&2
    return 1
  fi  
}

status() {
  if [ -f "$PIDFILE" ] && (ps -p $(cat "$PIDFILE") > /dev/null);
  then
    echo "Service is running" >&2
  else
    echo 'Service is not running' >&2
  fi  
}

uninstall() {
  echo -n "Are you really sure you want to uninstall this service? That cannot be undone. [yes|No] "
  local SURE
  read SURE
  if [ "$SURE" = "yes" ]; then
    stop
    rm -f "$PIDFILE"
    echo "Notice: log file is not to be removed: '$LOGFILE'" >&2
    update-rc.d -f $NAME remove
    rm -fv "$0"
  fi
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  uninstall)
    uninstall
    ;;
  status)
    status
    ;;  
  restart)
    stop
    start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|uninstall}"
esac
