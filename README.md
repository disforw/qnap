# QNAP Integration Re-write with Config-Flow

This is a complete re-write of the Core QNAP integration, adding config_flow and unique_ID. Using this custom componant will override the built-in QNAP integration.

## Installation

Due to this repository overriding an existing core integration, it will need to be added as a custom repository. Goto HACS - Custom Integrations - three dots at the top - Custom Repositories.
Paste: https://github.com/disforw/qnap


NOTE: All folder and drive entities will be disabled by default. You will need to go to the entities you want and enable them manually.
