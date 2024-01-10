from argparse import ArgumentParser
import logging
import os
from pprint import pp

from .auth import TokenAuth
from .vehicle import Vehicle
from .schema import RemoteCommand, Service

def main():
	LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
	logging.basicConfig(level=LOGLEVEL)

	parser = ArgumentParser(prog='NissanConnect')
	parser.add_argument('-u', '--username', required=True)
	parser.add_argument('-p', '--password', required=True)
	parser.add_argument('-v', '--vin', required=True)

	service_parsers = parser.add_subparsers(title='service', dest='service', help='The remote service')
	service_parsers.required = True

	for service in Service:
		sub_parser = service_parsers.add_parser(service.name.lower())
		choices = [rc.name.lower() for rc in RemoteCommand if rc.service == service]
		sub_parser.add_argument('-c', '--pin', default='', help='Pin for secure commands')
		if choices:
			sub_parser.add_argument('command', nargs='?', default=None, choices=choices, help='The command to send')

	args = parser.parse_args()

	auth = TokenAuth()
	auth.generate(args.username, args.password)

	vehicle = Vehicle(auth, args.vin, pin=args.pin)
	if getattr(args, 'command', None):
		command = RemoteCommand[args.command.upper()]
		r = vehicle.send_command(command)()
	else:
		service = Service[args.service.upper()]
		r = vehicle.get_status(service)
	pp(r)

if __name__ == '__main__':
	main()
