# Generated by the protocol buffer compiler.  DO NOT EDIT!

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)



DESCRIPTOR = descriptor.FileDescriptor(
  name='cec_messages.proto',
  package='ndn_pi_message',
  serialized_pb='\n\x12\x63\x65\x63_messages.proto\x12\x0endn_pi_message\"\xe4\x01\n\x1a\x44\x65vicesCapabilitiesMessage\x12Y\n\x12\x64\x65viceCapabilities\x18\x01 \x03(\x0b\x32=.ndn_pi_message.DevicesCapabilitiesMessage.DeviceCapabilities\x1ak\n\x12\x44\x65viceCapabilities\x12&\n\x06\x64\x65vice\x18\x01 \x02(\x0e\x32\x16.ndn_pi_message.Device\x12-\n\x0c\x63\x61pabilities\x18\x02 \x03(\x0e\x32\x17.ndn_pi_message.Command\"h\n\x0e\x43ommandMessage\x12+\n\x0b\x64\x65stination\x18\x01 \x02(\x0e\x32\x16.ndn_pi_message.Device\x12)\n\x08\x63ommands\x18\x02 \x03(\x0e\x32\x17.ndn_pi_message.Command*P\n\x06\x44\x65vice\x12\x06\n\x02TV\x10\x00\x12\x0f\n\x0bRECORDING_1\x10\x01\x12\x0e\n\nPLAYBACK_1\x10\x04\x12\x0e\n\nRESERVED_E\x10\x0e\x12\r\n\tBROADCAST\x10\x0f*\x9f\x01\n\x07\x43ommand\x12\x0b\n\x07STANDBY\x10\x00\x12\x06\n\x02ON\x10\x01\x12\x08\n\x04PLAY\x10\x02\x12\t\n\x05PAUSE\x10\x03\x12\x06\n\x02\x46\x46\x10\x04\x12\x06\n\x02RW\x10\x05\x12\x07\n\x03SEL\x10\x06\x12\x06\n\x02UP\x10\x07\x12\x08\n\x04\x44OWN\x10\x08\x12\x08\n\x04LEFT\x10\t\x12\t\n\x05RIGHT\x10\n\x12\x06\n\x02\x41S\x10\x0b\x12\t\n\x05SLEEP\x10\x0c\x12\n\n\x06TVMENU\x10\r\x12\x0b\n\x07\x44VDMENU\x10\x0e')

_DEVICE = descriptor.EnumDescriptor(
  name='Device',
  full_name='ndn_pi_message.Device',
  filename=None,
  file=DESCRIPTOR,
  values=[
    descriptor.EnumValueDescriptor(
      name='TV', index=0, number=0,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RECORDING_1', index=1, number=1,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='PLAYBACK_1', index=2, number=4,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RESERVED_E', index=3, number=14,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='BROADCAST', index=4, number=15,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=375,
  serialized_end=455,
)


_COMMAND = descriptor.EnumDescriptor(
  name='Command',
  full_name='ndn_pi_message.Command',
  filename=None,
  file=DESCRIPTOR,
  values=[
    descriptor.EnumValueDescriptor(
      name='STANDBY', index=0, number=0,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='ON', index=1, number=1,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='PLAY', index=2, number=2,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='PAUSE', index=3, number=3,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='FF', index=4, number=4,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RW', index=5, number=5,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='SEL', index=6, number=6,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='UP', index=7, number=7,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='DOWN', index=8, number=8,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='LEFT', index=9, number=9,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='RIGHT', index=10, number=10,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='AS', index=11, number=11,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='SLEEP', index=12, number=12,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='TVMENU', index=13, number=13,
      options=None,
      type=None),
    descriptor.EnumValueDescriptor(
      name='DVDMENU', index=14, number=14,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=458,
  serialized_end=617,
)


TV = 0
RECORDING_1 = 1
PLAYBACK_1 = 4
RESERVED_E = 14
BROADCAST = 15
STANDBY = 0
ON = 1
PLAY = 2
PAUSE = 3
FF = 4
RW = 5
SEL = 6
UP = 7
DOWN = 8
LEFT = 9
RIGHT = 10
AS = 11
SLEEP = 12
TVMENU = 13
DVDMENU = 14



_DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES = descriptor.Descriptor(
  name='DeviceCapabilities',
  full_name='ndn_pi_message.DevicesCapabilitiesMessage.DeviceCapabilities',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='device', full_name='ndn_pi_message.DevicesCapabilitiesMessage.DeviceCapabilities.device', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='capabilities', full_name='ndn_pi_message.DevicesCapabilitiesMessage.DeviceCapabilities.capabilities', index=1,
      number=2, type=14, cpp_type=8, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=160,
  serialized_end=267,
)

_DEVICESCAPABILITIESMESSAGE = descriptor.Descriptor(
  name='DevicesCapabilitiesMessage',
  full_name='ndn_pi_message.DevicesCapabilitiesMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='deviceCapabilities', full_name='ndn_pi_message.DevicesCapabilitiesMessage.deviceCapabilities', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=39,
  serialized_end=267,
)


_COMMANDMESSAGE = descriptor.Descriptor(
  name='CommandMessage',
  full_name='ndn_pi_message.CommandMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    descriptor.FieldDescriptor(
      name='destination', full_name='ndn_pi_message.CommandMessage.destination', index=0,
      number=1, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    descriptor.FieldDescriptor(
      name='commands', full_name='ndn_pi_message.CommandMessage.commands', index=1,
      number=2, type=14, cpp_type=8, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=269,
  serialized_end=373,
)

_DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES.fields_by_name['device'].enum_type = _DEVICE
_DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES.fields_by_name['capabilities'].enum_type = _COMMAND
_DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES.containing_type = _DEVICESCAPABILITIESMESSAGE;
_DEVICESCAPABILITIESMESSAGE.fields_by_name['deviceCapabilities'].message_type = _DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES
_COMMANDMESSAGE.fields_by_name['destination'].enum_type = _DEVICE
_COMMANDMESSAGE.fields_by_name['commands'].enum_type = _COMMAND
DESCRIPTOR.message_types_by_name['DevicesCapabilitiesMessage'] = _DEVICESCAPABILITIESMESSAGE
DESCRIPTOR.message_types_by_name['CommandMessage'] = _COMMANDMESSAGE

class DevicesCapabilitiesMessage(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  
  class DeviceCapabilities(message.Message):
    __metaclass__ = reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _DEVICESCAPABILITIESMESSAGE_DEVICECAPABILITIES
    
    # @@protoc_insertion_point(class_scope:ndn_pi_message.DevicesCapabilitiesMessage.DeviceCapabilities)
  DESCRIPTOR = _DEVICESCAPABILITIESMESSAGE
  
  # @@protoc_insertion_point(class_scope:ndn_pi_message.DevicesCapabilitiesMessage)

class CommandMessage(message.Message):
  __metaclass__ = reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _COMMANDMESSAGE
  
  # @@protoc_insertion_point(class_scope:ndn_pi_message.CommandMessage)

# @@protoc_insertion_point(module_scope)
