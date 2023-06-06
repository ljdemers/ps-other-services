# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
import grpc

from grpc.portservice.v1 import portservice_pb2 as grpc_dot_portservice_dot_v1_dot_portservice__pb2


class FindPortStub(object):
  """The port service definition.
  """

  def __init__(self, channel):
    """Constructor.

    Args:
      channel: A grpc.Channel.
    """
    self.FindNearestPort = channel.unary_unary(
        '/grpc_portservice_v1.FindPort/FindNearestPort',
        request_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.SerializeToString,
        response_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.FromString,
        )
    self.GetPort = channel.unary_unary(
        '/grpc_portservice_v1.FindPort/GetPort',
        request_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Data.SerializeToString,
        response_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.FromString,
        )
    self.FindClosestPorts = channel.stream_stream(
        '/grpc_portservice_v1.FindPort/FindClosestPorts',
        request_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.SerializeToString,
        response_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.FromString,
        )
    self.GetPortHistory = channel.stream_stream(
        '/grpc_portservice_v1.FindPort/GetPortHistory',
        request_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.SerializeToString,
        response_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.PortHistory.FromString,
        )


class FindPortServicer(object):
  """The port service definition.
  """

  def FindNearestPort(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetPort(self, request, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def FindClosestPorts(self, request_iterator, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')

  def GetPortHistory(self, request_iterator, context):
    # missing associated documentation comment in .proto file
    pass
    context.set_code(grpc.StatusCode.UNIMPLEMENTED)
    context.set_details('Method not implemented!')
    raise NotImplementedError('Method not implemented!')


def add_FindPortServicer_to_server(servicer, server):
  rpc_method_handlers = {
      'FindNearestPort': grpc.unary_unary_rpc_method_handler(
          servicer.FindNearestPort,
          request_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.FromString,
          response_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.SerializeToString,
      ),
      'GetPort': grpc.unary_unary_rpc_method_handler(
          servicer.GetPort,
          request_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Data.FromString,
          response_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.SerializeToString,
      ),
      'FindClosestPorts': grpc.stream_stream_rpc_method_handler(
          servicer.FindClosestPorts,
          request_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.FromString,
          response_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Port.SerializeToString,
      ),
      'GetPortHistory': grpc.stream_stream_rpc_method_handler(
          servicer.GetPortHistory,
          request_deserializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.Position.FromString,
          response_serializer=grpc_dot_portservice_dot_v1_dot_portservice__pb2.PortHistory.SerializeToString,
      ),
  }
  generic_handler = grpc.method_handlers_generic_handler(
      'grpc_portservice_v1.FindPort', rpc_method_handlers)
  server.add_generic_rpc_handlers((generic_handler,))
