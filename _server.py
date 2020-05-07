
import pyarrow as pa
import pyarrow.flight as fl


def create_table_int():
    data = [
        pa.array([1, 2, 3]),
        pa.array([4, 5, 6])
    ]
    return pa.Table.from_arrays(data, names=['column1', 'column2'])


def create_table_dict():
    keys = pa.array(["x", "y", "z"], type=pa.utf8())
    data = [
        pa.chunked_array([
            pa.DictionaryArray.from_arrays([0, 1, 2], keys),
            pa.DictionaryArray.from_arrays([0, 1, 2], keys)
        ]),
        pa.chunked_array([
            pa.DictionaryArray.from_arrays([1, 1, 1], keys),
            pa.DictionaryArray.from_arrays([2, 2, 2], keys)
        ])
    ]
    return pa.Table.from_arrays(data, names=['column1', 'column2'])

class FlightServer(fl.FlightServerBase):

    def __init__(self, location="grpc://0.0.0.0:8815", **kwargs):
        super(FlightServer, self).__init__(location, **kwargs)

        self.tables = {
            b'table_int': create_table_int(),
            b'table_dict': create_table_dict(),
        }

    def do_get(self, context, ticket):
        table = self.tables[ticket.ticket]
        return fl.RecordBatchStream(table)
        # return fl.GeneratorStream(table.schema, table.to_batches(max_chunksize=1024))

    def do_put(self, context, descriptor, reader, writer):
        ticket_name = b''.join(descriptor.path)
        self.tables[ticket_name] = reader.read_all()

    def get_flight_info(self, context, descriptor):
        ticket_name = b''.join(descriptor.path)
        if ticket_name in self.tables:
            table = self.tables[ticket_name]
            endpoints = [fl.FlightEndpoint(ticket_name, ["grpc://0.0.0.0:8815"])]
            return fl.FlightInfo(table.schema, descriptor, endpoints, table.num_rows, 0)

        raise KeyError("Unknown ticket name: {}".format(ticket_name))

    def get_schema(self, context, descriptor):
        info = self.get_flight_info(context, descriptor)
        return fl.SchemaResult(info.schema)

    def list_flights(self, context, criteria):
        for ticket_name in self.tables:
            descriptor = fl.FlightDescriptor.for_path(ticket_name)
            yield self.get_flight_info(context, descriptor)

    def list_actions(self, context):
        return [("greet", "returns greeting")]

    def do_action(self, context, action):
        if action.type == "greet":
            yield pa.flight.Result(b'Hello!')
        else:
            raise NotImplementedError("Unknown action: {}".format(action.type))


def main():
    FlightServer().serve()

if __name__ == '__main__':
    main()
