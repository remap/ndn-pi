# Configure NFD from samples
sudo cp /usr/local/etc/ndn/nfd.conf.sample /usr/local/etc/ndn/nfd.conf
sudo cp /usr/local/etc/ndn/client.conf.sample /usr/local/etc/ndn/client.conf

# Generate keys and establish root of trust
sudo mkdir -p /usr/local/etc/ndn/keys
ndnsec-keygen /`whoami` | ndnsec-install-cert -
ndnsec-cert-dump -i /`whoami` > default.ndncert
sudo mv default.ndncert /usr/local/etc/ndn/keys/default.ndncert

# Generate keys for app
#serial=`cat /proc/cpuinfo | grep "Serial" | awk -F":" '{print $2}' | tr -d ' '`
#ndnsec-keygen /home/dev/$serial | ndnsec-install-cert -
#ndnsec-cert-dump -i /home/dev/$serial | sudo ndnsec-install-cert - # Also install as root cert because sensor publisher must run as sudo
#ndnsec-cert-dump -i /home/dev/$serial > default.ndncert
#sudo mv default.ndncert /usr/local/etc/ndn/keys/default.ndncert

#ndnsec-set-default /pi
