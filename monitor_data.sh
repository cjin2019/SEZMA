top -i 10 -stats time,pid,command,cpu,mem | grep videonetworkapp --line-buffered > videonetworkapp.csv &
top -i 10 -stats time,pid,command,cpu,mem | grep zoom.us --line-buffered > zoom.csv & 
wait     
