#!/bin/bash

SERVICE_FILE="monitoragent.sh"
DAEMON_FILE="Agent.py"
SYSTEM_CHECK="SystemCheck.py"
NETWORK_CHECK="NetworkCheck.py"

echo "--- Download monitoragent init script ---"
wget -q -O "$SERVICE_FILE" 'https://raw.githubusercontent.com/N42Inc/server_monitor/master/monitoragent.sh'
chmod +x "$SERVICE_FILE"
echo ""

echo "--- Download agent ---"
wget -q -O "$DAEMON_FILE" 'https://raw.githubusercontent.com/N42Inc/server_monitor/master/Agent.py'
chmod +x "$DAEMON_FILE"
echo ""

echo "--- Download checks ---"
wget -q -O "$SYSTEM_CHECK" 'https://raw.githubusercontent.com/N42Inc/server_monitor/master/SystemCheck.py'
chmod +x "$SYSTEM_CHECK"
wget -q -O "$NETWORK_CHECK" 'https://raw.githubusercontent.com/N42Inc/server_monitor/master/NetworkCheck.py'
chmod +x "$NETWORK_CHECK"
echo ""

#echo "--- Customize ---"
#echo "I'll now ask you some information to customize script"
#echo "Press Ctrl+C anytime to abort."
#echo "Empty values are not accepted."
#echo ""

prompt_token() {
  local VAL=""
  while [ "$VAL" = "" ]; do
    echo -n "${2:-$1} : "
    read VAL
    if [ "$VAL" = "" ]; then
      echo "Please provide a value"
    fi
  done
  VAL=$(printf '%q' "$VAL")
  eval $1=$VAL
  sed -i "s/<$1>/$(printf '%q' "$VAL")/g" $SERVICE_FILE
}

#prompt_token 'NAME'        'Service name'
#if [ -f "/etc/init.d/$NAME" ]; then
#  echo "Error: service '$NAME' already exists"
#  exit 1
#fi

#prompt_token 'DESCRIPTION' ' Description'
#prompt_token 'COMMAND'     '     Command'
#prompt_token 'USERNAME'    '        User'
#if ! id -u "$USERNAME" &> /dev/null; then
#  echo "Error: user '$USERNAME' not found"
#  exit 1
#fi

NAME="monitoragent"

echo ""

echo "--- Installation ---"
if [ ! -w /etc/init.d ]; then
  echo "You don't gave me enough permissions to install service myself."
  echo "That's smart, always be really cautious with third-party shell scripts!"
  echo "You should now type those commands as superuser to install and run your service:"
  echo ""
  echo "   mv \"$SERVICE_FILE\" \"/etc/init.d/$NAME\""
  echo "   touch \"/var/log/$NAME.log\" && chown \"$USERNAME\" \"/var/log/$NAME.log\""
  echo "   update-rc.d \"$NAME\" defaults"
  echo "   service \"$NAME\" start"
else
  echo "[----------Installation started ---------------]"
  echo ""
  echo "[------------Agent Cleanup Started(Removing Old Agents for fresh installation)-----------]"   
  if service --status-all |& grep -Fq 'monitoragent';
  then 
       service monitoragent stop
       echo "Please type yes as the answer as we are removing old Agents"   
       service monitoragent uninstall    
  fi	
  if [ -f /opt/agents/monitor/SystemCheck.py ];
  then 
      rm -r /opt/agents/monitor/
      rm /etc/init.d/monitoragent        
  fi
  echo "[------------Agent Cleanup Ended-----------]"   
  echo ""
  if [[ ! -e /opt/agents/monitor/ ]]; 
  then
       #echo "creating agents directory for installing monitoragent"	
       mkdir -p /opt/agents/monitor/
       if [ $? -ne 0 ];
       then
            echo "could not create directory : /opt/agents/monitor/"
            exit 1
       fi
  fi  
  echo "[------------Copying the Agents Started -----------]"   
  #echo "mv \"$DAEMON_FILE\" \"/opt/agents/monitor\""
  mv -v "$DAEMON_FILE" "/opt/agents/monitor/"
  mv -v "$SYSTEM_CHECK" "/opt/agents/monitor/"
  mv -v "$NETWORK_CHECK" "/opt/agents/monitor/"
  #echo "mv \"$SERVICE_FILE\" \"/etc/init.d/$NAME\""
  mv -v "$SERVICE_FILE" "/etc/init.d/$NAME"
  echo "[------------Copying the Agents Ended --------------]"   
  #echo "touch \"/var/log/myloop.log\""
  #touch "/var/log/$NAME.log" && chown "$USERNAME" "/var/log/$NAME.log"
  #echo "3. update-rc.d \"$NAME\" defaults"
  #update-rc.d "$NAME" defaults
  echo ""
  #echo "service \"$NAME\" start"
  sudo service "$NAME" start
  echo ""
  echo "!!!!!!! Installation succesful ! Have that Mc Donalds IceCream !!!!!!!!!!."
fi
echo ""
echo ""
echo ""
echo "[--------------Agent usage Instructions------------------]"
echo "To start the agent : service monitoragent start"
echo "To stop the agent : service monitoragent stop"
echo "To uninstall the agent : service monitoragent uninstall"
echo "[--------------------------------------------------------]"
#echo "---Uninstall instructions ---"
#echo "The service can uninstall itself:"
#echo "    service \"$NAME\" uninstall"
#echo "It will simply run update-rc.d -f \"$NAME\" remove && rm -f \"/etc/init.d/$NAME\""
#echo ""
#echo "--- Terminated ---"
