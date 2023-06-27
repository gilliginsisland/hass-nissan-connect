from argparse import ArgumentParser
import logging
import os
from pprint import pp

from .auth import Auth
from .vehicle import Vehicle
from .schema import Service

def main():
	LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
	logging.basicConfig(level=LOGLEVEL)

	parser = ArgumentParser(prog='NissanConnect')
	parser.add_argument('-u', '--username', required=True)
	parser.add_argument('-p', '--password', required=True)
	parser.add_argument('-v', '--vin', required=True)

	method_parsers = parser.add_subparsers(title='methods', dest='method', help='The http method')
	method_parsers.required = True

	get_parsers = method_parsers.add_parser('get').add_subparsers(
		title='services', dest='service', help='The service to get the status of',
		)
	get_parsers.required = True

	post_parsers = method_parsers.add_parser('post').add_subparsers(
		title='services', dest='service', help='The service to post a command to',
		)
	post_parsers.required = True

	for service in Service:
		get_parser = get_parsers.add_parser(service.value)
		get_parser.add_argument('request_id', nargs='?', default=None, help='The request_id to check status of')

		if service.command:
			choices = [choice.value for choice in service.command]
			post_parser = post_parsers.add_parser(service.value)
			post_parser.add_argument('-c', '--pin', default=None, help='Pin for secure commands')
			post_parser.add_argument('command', choices=choices, help='The command to send')

	args = parser.parse_args()

	auth = Auth()
	auth.fetch_tokens(args.username, args.password)

	vehicle = Vehicle(auth, args.vin)
	service = Service(args.service)
	if args.method == 'get':
		r = vehicle.get(service)
	elif service.command:
		command = service.command(args.command)
		r = vehicle.post(service, command=command, pin=args.pin)
	else:
		raise ValueError(f'Invalid service command combination. [{args.service}, {args.command}]')
	pp(r)

if __name__ == '__main__':
	main()
