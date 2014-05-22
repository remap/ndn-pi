sudo apt-get install build-essential
sudo apt-get install openssl expat libpcap-dev
sudo apt-get install libssl-dev libsqlite3-dev libcrypto++-dev libboost-all-dev

git clone https://github.com/named-data/ndnx.git
git clone https://github.com/named-data/ndn-cpp.git
git clone https://github.com/named-data/PyNDN2.git

# Not needed on pi if cross-compiling
#git clone https://github.com/named-data/ndn-cxx.git
#git clone https://github.com/named-data/NFD.git
#git clone https://github.com/named-data/repo-ng.git

echo "export PYTHONPATH=$PYTHONPATH:$HOME/ndn/PyNDN2/python:$HOME/ndn/ndn-pi" >> ~/.bashrc
echo "ipv6" >> /etc/modules
