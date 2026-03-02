# OEJP Kraken

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

Home Assistant custom integration for Octopus Energy Japan (OEJP) Kraken API.

## Features

- 🔌 **Real-time Power Monitoring** - Current power consumption in watts
- 📊 **Daily Consumption Tracking** - Today's electricity usage in kWh
- 💴 **Current Rate Display** - Live electricity rate in JPY/kWh
- 🔄 **Automatic Token Refresh** - Secure authentication with automatic token management
- 📱 **Config Flow Setup** - Easy UI-based configuration

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant
2. Click on "Integrations"
3. Click the menu (three dots) in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/tamatyan99/oejp-kraken` as an Integration
6. Click "Add"
7. Find "OEJP Kraken" in the list and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/oejp_kraken` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "OEJP Kraken"
4. Enter your Octopus Energy Japan credentials:
   - Email address
   - Password
5. Optionally adjust the update interval (default: 300 seconds)

## Sensors

This integration provides the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.oejp_current_power` | Current power consumption | W |
| `sensor.oejp_today_consumption` | Today's electricity consumption | kWh |
| `sensor.oejp_current_rate` | Current electricity rate | JPY/kWh |

## Requirements

- Home Assistant 2023.1.0 or newer
- Octopus Energy Japan account

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/tamatyan99/oejp-kraken/issues).

## License

[MIT License](LICENSE)
