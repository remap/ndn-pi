# TODO: Make sure $1 is ip address
NFDC_CREATE_OUT=`nfdc create udp://$1`
echo $NFDC_CREATE_OUT
# |
faceid=`echo $NFDC_CREATE_OUT | awk '{ print $5 }' | awk -F',' '{ print $1 }'`
nfdc add-nexthop / $faceid
