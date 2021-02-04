ssh root@178.128.214.106 "
cd i-host-backend/
git pull
sudo service daphane restart
sudo service sheduler restart
echo "sheduler and daphane restarted on ihost dev"
exit
"