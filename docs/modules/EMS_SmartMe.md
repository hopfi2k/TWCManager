# SmartMe EMS Module

This module allows querying of [smart-me.com](https://smart-me.com/swagger/ui/index) inverters.

Note: Only Generation values are supported by this module.

## Introduction

| **Parameter** | **Value** |
| ------------- | --------- |
| enabled       | *required* Boolean value, ```true``` or ```false```. Determines whether we will poll the SmartMe API |
| password      | *required* The password for accessing the API |
| serialNumber  | *required* The Serial Number of the Inverter to query |
| username      | *required* The username for accessing the API |

## JSON Configuration Example

The following configuration should be placed under the "sources" section of the config.json file in your installation, and will enable SmartMe EMS polling.

```
"SmartMe": {
  "enabled": true,
  "username": "username",
  "password": "password",
  "serialNumber": "ABC1234"
}

```
