## Introduction
A [NIP-57](https://github.com/nostr-protocol/nips/blob/master/57.md) server that allows you recieve zaps on nostr, forwarded to your lightning node running on TOR. This server allows you to create a [Lightning Address](https://github.com/andrerfneves/lightning-address/blob/master/DIY.md) by slecting a username and using a your own domain.


## How it works?

![zap_server](https://github.com/UTXOnly/zap_server/assets/49233513/768fe50f-c677-48d4-af84-a18878b05aaa)


## Prerequisites 
* An Ubuntu server reachable by a public IP (tested on 22.04 amd64 host server )
* Your own domain
* A Lightning node running [LND](https://github.com/lightningnetwork/lnd/tree/master)

## What these scripts do
* Installs and configures `nginx` reverse proxy server
  * Uses `certbot` to get TLS certificate for domain
* Deploys Flask server to respond to clients with Lightning invoices

## What you need to do

* Clone the repository
```
git clone https://github.com/UTXOnly/zap_server.git
```

* Edit the `.env` file to include your node and `LUD-16` identifier using a command line text editor like `nano`.
```
nano .env
```

### Setup the server

* Start the CLI menu
```
python3 menu.py
```
![Screenshot from 2023-11-24 23-49-04](https://github.com/UTXOnly/zap_server/assets/49233513/afdc66de-3213-403d-af41-c638bf4be265)

### Using the command line interface (CLI)

* Option 1 runs the server setup script, downloads dependencies, installs and configures the NGINX proxy server
* Option 2 starts the Flask server to begin responding to clients requests for lightning invoices
* Option 3 stops the Flask server (Will not respond to requests for invoices)
* Option 4 exits the CLI menu

## To Do
- [] Update `.env` file permissions, potentially encrypt?
- [] Add UFW firewall rules
- [] Improve error handling
- [] Add unit tests
