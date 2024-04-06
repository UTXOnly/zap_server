## Introduction
A [NIP-57](https://github.com/nostr-protocol/nips/blob/master/57.md) server that allows you recieve zaps on nostr, forwarded to your lightning node running on Tor. This server allows you to create a [Lightning Address](https://github.com/andrerfneves/lightning-address/blob/master/DIY.md) by selecting a username and using your own domain. YOu can run this zap server on a $5 a month VPS, I have included some guides in the additional resouces section of this README to help guide users if need be.

The Zapserver can fetch invoices can fetch invoices over tor or Wireguard VPN tunnel. It is strongly recomended to use a Wireguard VPN tunnel to fetch invoices as tor is very slow to return invoices and the person zapping you will probably not wait around for it. You can create a Wireguard VPN tunnel to connect to your tor node by following the [wireguard_setup](https://github.com/UTXOnly/zap_server/blob/wireguard_doc/docs/wireguard_setup.md) doc.

#### Tradeoffs
* Recieve zaps directly to you lightning node
  * Custody your own sats and don't need to worry about sweeping them from a custodial wallet or getting rug pulled by a custodian
* Create invoices from your own lightning node and could potentially share information about your node (for example node pubkey, channel balances, UTXOs). See [this article](https://abytesjourney.com/lightning-privacy/#:~:text=you%20receive%20payments.-,Invoices,-Typically%2C%20whenever%20you) for more information about lightning privacy
* Must maintain sufficent inbound liquidity to recieve zaps and have some path between the sender's wallet and your node
* Storing an [invoice.macaroon](https://docs.lightning.engineering/lightning-network-tools/lnd/macaroons#:~:text=invoice.macaroon,write%3B%20onchain%3A%20read) on your zap server which can read and create invoices on your node, protect this!


## How it works?

![zap_server](https://github.com/UTXOnly/zap_server/assets/49233513/566c52c7-23ed-42ea-8f49-657b1f8a795a)





## Prerequisites 
* An Linux server reachable by a public IP (tested on Ubuntu 22.04 amd64 host)
* Your own domain
* A Lightning node running [LND](https://github.com/lightningnetwork/lnd/tree/master)

## What these scripts do
* Installs all dependencies and configures `nginx` reverse proxy server
  * This script will overwrite anything in `etc/nginx/sites-available/default`
  * Uses `certbot` to get TLS certificate for domain
* Deploys Flask server to respond to clients with Lightning invoices

## What you need to do

* Getting your LND REST information and `invoice.macaroon`, this example shows getting this information from a [Raspiblitz](https://github.com/raspiblitz/raspiblitz) node.

![Screen Recording 2023-11-25 at 12 44 26 AM](https://github.com/UTXOnly/zap_server/assets/49233513/34f16443-74f6-46f5-ab35-999ec6b46697)

![Image 2023-11-25 at 12 45 17 AM](https://github.com/UTXOnly/zap_server/assets/49233513/e665c34c-a9a4-4756-8a31-f84ec8b6a152)


* Clone the repository
```
git clone https://github.com/UTXOnly/zap_server.git
```

* Edit the `.env` file to include your node and `LUD-16` identifier using a command line text editor like `nano`.
```
nano .env
```

* Example `.env` file:

```
LND_ONION_ADDRESS=''#"<YOUR_LND_NODE_ONION_ADDRESS>" For example, xyzdasdsadsa.onion, leave blank if using Wireguard VPN
VPN_HOST=''# <YOUR_HOST_IP> for you VPN client
LND_REST_PORT=8080 #Default LND REST port is 8080, in most cases you can leave this untouched
LND_INVOICE_MACAROON_HEX="<YOUR_LND_INVOICE_HEX_HERE>"
INTERNET_IDENTIFIER="<IDENTIFIER_HERE>" ## Add the value on the left side of your LNURL identifier for example if your LNURL identifier is "nabismo@nostpypy.lol" you would add "nabismo" here
HEX_PUBKEY='' # <YOUR_NOSTR_HEX_PUBKEY> 
HEX_PRIV_KEY='' #<YOUR_NOSTR_HEX_PRIV_KEY>
DOMAIN="<YOUR_DOMAIN_HERE>" # For example nostpy.lol
CONTACT=<YOUR_EMAIL_ADDRESS> #Enter your email address for the certbot command to get emails about your TLS certificate when it is near expiration
NGINX_FILE_PATH=/etc/nginx/sites-available/default #Leave this untouched
```
* You can get the `HEX` version of your public key from certrain clients and signing extensions
  * You can also use [NostrDebug Converter Tool](https://nostrdebug.com/converter/) to convert your `npub` to a `HEX` value

### Setup the server

* Start the CLI menu
```
python3 menu.py
```
* `menu.py` is the main process used to control the server 
![Screenshot from 2023-11-24 23-49-04](https://github.com/UTXOnly/zap_server/assets/49233513/afdc66de-3213-403d-af41-c638bf4be265)

### Using the command line interface (CLI)

* Option 1 runs the server setup script, downloads dependencies, installs and configures the NGINX proxy server
* Option 2 starts the Flask server to begin responding to clients requests for lightning invoices
* Option 3 stops the Flask server (Will not respond to requests for invoices)
* Option 4 exits the CLI menu

### Additional Resources
* [Creating a droplet on Digital Ocean ( A virtual Private Server)](https://docs.digitalocean.com/developer-center/onboarding-working-with-digitalocean-droplets/)
* [Intial Ubuntu 22.04 server setup on Digital Ocean](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04)


## To Do
- [] Update `.env` file permissions, potentially encrypt?
- [] Possibly use [Nsecbunker](https://github.com/kind-0/nsecbunkerd)?
- [] Add UFW firewall rules
- [] Improve error handling
- [] Add unit tests
- [x] Add support for Wireguard VPN tunnel connect method
- [] Create Docker container deployment option
- [] Add option to diable the Nginx setup portion ofthe setup script if user is already running Nginx
- [x] Add response to Nostr client to confirm zap completed succsessfully

## Contributing

Anyone is welcome and encourges to contribute! If you want to add feature, feel free to open a pull request. 

If you find a bug, please open an issue and include any relevant details, for example:
* Operating system and version
* Python version
* Expected behavior
* Actual behavior
* Any logs that might be helpful in troubleshooting
