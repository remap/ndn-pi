from pyndn import Interest
from pyndn import Name
import app.cec_messages_pb2 as pb

m = pb.CommandMessage()
m.destination = pb.TV
m.commands.append(pb.AS)
m.commands.append(pb.SLEEP)
m.commands.append(pb.SLEEP)
m.commands.append(pb.YOUSHALLNOTPASS)
from pyndn.encoding import ProtobufTlv
encodedMessage = ProtobufTlv.encode(m)
interest = Interest(Name("/home/cec").append("1234568790").append(encodedMessage))

decodedMessage = pb.CommandMessage()
ProtobufTlv.decode(decodedMessage, interest.getName().get(3).getValue())
