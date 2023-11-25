## Introduction
A server that allows you recieve zaps on nostr, forwarded to your lightning node running on TOR.

## How it works?

![zap_server](https://github.com/UTXOnly/zap_server/assets/49233513/768fe50f-c677-48d4-af84-a18878b05aaa)


## Prerequisites 
* An Ubuntu server reachable by a public IP (tested on 22.04 amd64 host server )
* Your own domain
* A Lightning node running LND

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
