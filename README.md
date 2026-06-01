# Home Assistant Nissan Connect

Home Assistant integration for NissanConnect Services.

## Support

This integration supports NissanConnect Services accounts in the United States for vehicles that use SiriusXM satellite service for remote control.

An active NissanConnect Services subscription is required. The API may still expose all supported remote commands even when the Nissan app only shows a subset, such as lock and unlock.

## Features

- Door, hood, and hatch status
- Vehicle warning indicators
- Vehicle door lock and unlock
- Tire pressure sensors
- GPS device tracker
- Remote engine start and stop
- Remote horn and lights

## Configuration

Add one config entry per Nissan account.

You must create a config subentry for each VIN that you would like to expose, auto discovery is not supported.

The Nissan API does not provide push updates for this integration at the moment, so Home Assistant polls the API for updates.

## Contributing

Pull requests are welcome!
