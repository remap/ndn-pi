echo "# nfd-start"
nfd-start

echo "# sleep 10"
sleep 10

echo "# python test_publish_async_ss.py &"
python test_publish_async_ss.py &

echo "# sleep 10"
sleep 10

echo "# python test_get_async_ss.py"
python test_get_async_ss.py

echo "# sleep 10"
sleep 10

echo "# nfd-stop"
nfd-stop
