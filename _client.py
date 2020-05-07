
import argparse
import sys

import pyarrow as pa
import pyarrow.flight as fl

def get_by_ticket(args, client):
    ticket_name = args.name
    response = client.do_get(fl.Ticket(ticket_name)).read_all()
    print_response(response)

def get_by_ticket_pandas(args, client):
    ticket_name = args.name
    response = client.do_get(fl.Ticket(ticket_name)).read_pandas()
    print_response(response)

def get_schema(args, client):
    path = args.path
    response = client.get_schema(fl.FlightDescriptor.for_path(path))
    print_response(response.schema)

def get_endpoints(args, client):
    path = args.path
    response = client.get_flight_info(fl.FlightDescriptor.for_path(path))
    print_response(response.endpoints)

def do_put(args, client):
    path = args.path
    values = args.values.split(',')

    table = pa.Table.from_arrays([pa.array(values)], names=['column1'])

    writer, _ = client.do_put(fl.FlightDescriptor.for_path(path), table.schema)
    writer.write_table(table, len(values))
    writer.close()

def list_actions(args, client):
    response = client.list_actions()
    print_response(response)

def do_action(args, client):
    action_type = args.type
    response = client.do_action(pa.flight.Action(action_type, pa.allocate_buffer(0)))
    print("=== Response ===")
    for r in response:
        print(r.body.to_pybytes())
        print("================")

def list_flights(args, client):
    response = client.list_flights()
    print("=== Response ===")
    for r in response:
        print(r.descriptor)
        print(r.schema)
        print(r.endpoints)
        print(r.total_records)
        print("================")

def print_response(data):
    print("=== Response ===")
    print(data)
    print("================")

def main():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers()

    cmd_get_by_t = subcommands.add_parser('get_by_ticket')
    cmd_get_by_t.set_defaults(action='get_by_ticket')
    cmd_get_by_t.add_argument('-n', '--name', type=str, help="Name of the ticket to fetch.")

    cmd_get_by_tp = subcommands.add_parser('get_by_ticket_pandas')
    cmd_get_by_tp.set_defaults(action='get_by_ticket_pandas')
    cmd_get_by_tp.add_argument('-n', '--name', type=str, help="Name of the ticket to fetch.")

    cmd_get_schema = subcommands.add_parser('get_schema')
    cmd_get_schema.set_defaults(action='get_schema')
    cmd_get_schema.add_argument('-p', '--path', type=str, help="Descriptor path.")

    cmd_get_endpoints = subcommands.add_parser('get_endpoints')
    cmd_get_endpoints.set_defaults(action='get_endpoints')
    cmd_get_endpoints.add_argument('-p', '--path', type=str, help="Descriptor path.")

    cmd_do_put = subcommands.add_parser('do_put')
    cmd_do_put.set_defaults(action='do_put')
    cmd_do_put.add_argument('-p', '--path', type=str, help="Descriptor path.")
    cmd_do_put.add_argument('-v', '--values', type=str, help="Values to put on server.")

    cmd_list_actions = subcommands.add_parser('list_actions')
    cmd_list_actions.set_defaults(action='list_actions')

    cmd_do_action = subcommands.add_parser('do_action')
    cmd_do_action.set_defaults(action='do_action')
    cmd_do_action.add_argument('-t', '--type', type=str, help="Type of action.")

    cmd_list_flights = subcommands.add_parser('list_flights')
    cmd_list_flights.set_defaults(action='list_flights')

    args = parser.parse_args()
    if not hasattr(args, 'action'):
        parser.print_help()
        sys.exit(1)

    commands = {
        'get_by_ticket': get_by_ticket,
        'get_by_ticket_pandas': get_by_ticket_pandas,
        'get_schema': get_schema,
        'get_endpoints': get_endpoints,
        'list_flights': list_flights,
        'do_put': do_put,
        'list_actions': list_actions,
        'do_action': do_action,
    }

    client = fl.connect("grpc://0.0.0.0:8815")

    commands[args.action](args, client)


if __name__ == '__main__':
    main()
