# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: grpc/portservice/v1/portservice.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='grpc/portservice/v1/portservice.proto',
  package='grpc_portservice_v1',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n%grpc/portservice/v1/portservice.proto\x12\x13'
                   'grpc_portservice_v1\"\x07\n\x05\x45mpty\"\x91\x01\n\x08'
                   'Position\x12\x11\n\ttype_code\x18\x01 \x01(\t\x12\x11\n'
                   '\ttimestamp\x18\x02 \x01(\x05\x12\x0e\n\x06source\x18\x03'
                   ' \x01(\t\x12\x10\n\x08latitude\x18\x04 \x01(\x02\x12\x11'
                   '\n\tlongitude\x18\x05 \x01(\x02\x12\x14\n\x0csog_reported'
                   '\x18\x06 \x01(\x02\x12\x14\n\x0c\x63og_reported\x18\x07'
                   ' \x01(\x02\"\xcd\x01\n\x04Port\x12\x0c\n\x04\x63ode'
                   '\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02'
                   ' \x01(\t\x12\x14\n\x0c\x63ountry_code\x18\x03 \x01'
                   '(\t\x12\x10\n\x08latitude\x18\x04 \x01(\x02\x12\x11\n\t'
                   'longitude\x18\x05 \x01(\x02\x12\x13\n\x0biso_country'
                   '\x18\x06 \x01(\t\x12\x13\n\x0bport_source\x18\x07'
                   ' \x01(\t\x12\x13\n\x0bihs_port_id\x18\x08 \x01(\t\x12'
                   '\x19\n\x11world_port_number\x18\t \x01(\t\x12\x14\n'
                   '\x0c\x63ountry_name\x18\n \x01(\t\"g\n\x0bPortHistory'
                   '\x12\'\n\x04port\x18\x01 \x01(\x0b\x32\x19'
                   '.grpc_portservice_v1.Port'
                   '\x12\x17\n\x0ftimestamp_enter\x18\x02'
                   ' \x01(\x05\x12\x16\n\x0etimestamp_exit\x18\x03 \x01'
                   '(\x05\"$\n\x04\x44\x61ta\x12\r\n\x05\x66ield\x18\x01'
                   ' \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t2\xc9\x02\n\x08'
                   '\x46indPort\x12M\n\x0f\x46indNearestPort\x12\x1d'
                   '.grpc_portservice_v1.Position\x1a\x19'
                   '.grpc_portservice_v1.Port\"\x00\x12'
                   '\x41\n\x07GetPort\x12\x19.grpc_portservice_v1.Data\x1a\x19'
                   '.grpc_portservice_v1.Port\"\x00\x12R\n'
                   '\x10\x46indClosestPorts'
                   '\x12\x1d.grpc_portservice_v1.Position'
                   '\x1a\x19.grpc_portservice_v1.Port'
                   '\"\x00(\x01\x30\x01\x12W\n\x0eGetPortHistory\x12\x1d'
                   '.grpc_portservice_v1.Position'
                   '\x1a .grpc_portservice_v1.PortHistory'
                   '\"\x00(\x01\x30\x01\x62\x06proto3')
)




_EMPTY = _descriptor.Descriptor(
  name='Empty',
  full_name='grpc_portservice_v1.Empty',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=62,
  serialized_end=69,
)


_POSITION = _descriptor.Descriptor(
  name='Position',
  full_name='grpc_portservice_v1.Position',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type_code', full_name='grpc_portservice_v1.Position.type_code', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='grpc_portservice_v1.Position.timestamp', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='source', full_name='grpc_portservice_v1.Position.source', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='latitude', full_name='grpc_portservice_v1.Position.latitude', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='longitude', full_name='grpc_portservice_v1.Position.longitude', index=4,
      number=5, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='sog_reported', full_name='grpc_portservice_v1.Position.sog_reported', index=5,
      number=6, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='cog_reported', full_name='grpc_portservice_v1.Position.cog_reported', index=6,
      number=7, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=72,
  serialized_end=217,
)


_PORT = _descriptor.Descriptor(
  name='Port',
  full_name='grpc_portservice_v1.Port',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='code', full_name='grpc_portservice_v1.Port.code', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='name', full_name='grpc_portservice_v1.Port.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='country_code',
      full_name='grpc_portservice_v1.Port.country_code', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='latitude', full_name='grpc_portservice_v1.Port.latitude', index=3,
      number=4, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='longitude',
      full_name='grpc_portservice_v1.Port.longitude', index=4,
      number=5, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='iso_country',
      full_name='grpc_portservice_v1.Port.iso_country', index=5,
      number=6, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='port_source',
      full_name='grpc_portservice_v1.Port.port_source', index=6,
      number=7, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ihs_port_id',
      full_name='grpc_portservice_v1.Port.ihs_port_id', index=7,
      number=8, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='world_port_number',
      full_name='grpc_portservice_v1.Port.world_port_number', index=8,
      number=9, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='country_name',
      full_name='grpc_portservice_v1.Port.country_name', index=9,
      number=10, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=220,
  serialized_end=425,
)


_PORTHISTORY = _descriptor.Descriptor(
  name='PortHistory',
  full_name='grpc_portservice_v1.PortHistory',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='port', full_name='grpc_portservice_v1.PortHistory.port', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timestamp_enter',
      full_name='grpc_portservice_v1.PortHistory.timestamp_enter', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='timestamp_exit',
      full_name='grpc_portservice_v1.PortHistory.timestamp_exit', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=427,
  serialized_end=530,
)


_DATA = _descriptor.Descriptor(
  name='Data',
  full_name='grpc_portservice_v1.Data',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='field', full_name='grpc_portservice_v1.Data.field', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='grpc_portservice_v1.Data.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=532,
  serialized_end=568,
)

_PORTHISTORY.fields_by_name['port'].message_type = _PORT
DESCRIPTOR.message_types_by_name['Empty'] = _EMPTY
DESCRIPTOR.message_types_by_name['Position'] = _POSITION
DESCRIPTOR.message_types_by_name['Port'] = _PORT
DESCRIPTOR.message_types_by_name['PortHistory'] = _PORTHISTORY
DESCRIPTOR.message_types_by_name['Data'] = _DATA
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Empty = _reflection.GeneratedProtocolMessageType(
  'Empty', (_message.Message,), {
  'DESCRIPTOR' : _EMPTY,
  '__module__' : 'grpc.portservice.v1.portservice_pb2'
  # @@protoc_insertion_point(class_scope:grpc_portservice_v1.Empty)
  })
_sym_db.RegisterMessage(Empty)

Position = _reflection.GeneratedProtocolMessageType(
  'Position', (_message.Message,), {
  'DESCRIPTOR' : _POSITION,
  '__module__' : 'grpc.portservice.v1.portservice_pb2'
  # @@protoc_insertion_point(class_scope:grpc_portservice_v1.Position)
  })
_sym_db.RegisterMessage(Position)

Port = _reflection.GeneratedProtocolMessageType(
  'Port', (_message.Message,), {
  'DESCRIPTOR' : _PORT,
  '__module__' : 'grpc.portservice.v1.portservice_pb2'
  # @@protoc_insertion_point(class_scope:grpc_portservice_v1.Port)
  })
_sym_db.RegisterMessage(Port)

PortHistory = _reflection.GeneratedProtocolMessageType(
  'PortHistory', (_message.Message,), {
  'DESCRIPTOR' : _PORTHISTORY,
  '__module__' : 'grpc.portservice.v1.portservice_pb2'
  # @@protoc_insertion_point(class_scope:grpc_portservice_v1.PortHistory)
  })
_sym_db.RegisterMessage(PortHistory)

Data = _reflection.GeneratedProtocolMessageType(
  'Data', (_message.Message,), {
  'DESCRIPTOR' : _DATA,
  '__module__' : 'grpc.portservice.v1.portservice_pb2'
  # @@protoc_insertion_point(class_scope:grpc_portservice_v1.Data)
  })
_sym_db.RegisterMessage(Data)



_FINDPORT = _descriptor.ServiceDescriptor(
  name='FindPort',
  full_name='grpc_portservice_v1.FindPort',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=571,
  serialized_end=900,
  methods=[
  _descriptor.MethodDescriptor(
    name='FindNearestPort',
    full_name='grpc_portservice_v1.FindPort.FindNearestPort',
    index=0,
    containing_service=None,
    input_type=_POSITION,
    output_type=_PORT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetPort',
    full_name='grpc_portservice_v1.FindPort.GetPort',
    index=1,
    containing_service=None,
    input_type=_DATA,
    output_type=_PORT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='FindClosestPorts',
    full_name='grpc_portservice_v1.FindPort.FindClosestPorts',
    index=2,
    containing_service=None,
    input_type=_POSITION,
    output_type=_PORT,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='GetPortHistory',
    full_name='grpc_portservice_v1.FindPort.GetPortHistory',
    index=3,
    containing_service=None,
    input_type=_POSITION,
    output_type=_PORTHISTORY,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_FINDPORT)

DESCRIPTOR.services_by_name['FindPort'] = _FINDPORT

# @@protoc_insertion_point(module_scope)
