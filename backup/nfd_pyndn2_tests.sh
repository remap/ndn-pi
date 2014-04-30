echo "# nfd-start"
nfd-start

echo "# sleep 10"
sleep 10

echo "# python ~/ndn/PyNDN2/tests/test_publish_async_nfd.py &"
python ~/ndn/PyNDN2/tests/test_publish_async_nfd.py &

echo "# sleep 10"
sleep 10

echo "# python ~/ndn/PyNDN2/tests/test_get_async_1.py"
python ~/ndn/PyNDN2/tests/test_get_async_1.py

echo "# sleep 10"
sleep 10

echo "# nfd-stop"
nfd-stop
