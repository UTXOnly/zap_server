## Setup 

### Wireguard Server Setup

1. Update your server

```
apt-get update && apt-get upgrade -y
```
2. Enable forwarding of IP packets
```
sudo sed '/net.ipv4.ip_forward=1/s/^#//' -i /etc/sysctl.conf
sysctl -p
```
3. Install Wireguard

```
apt-get install wireguard
```

4. Go to to the Wireguard config `cd /etc/wireguard` and then run the following command to generate the public and private keys for the server.

```
umask 077; wg genkey | tee privatekey | wg pubkey > publickey
```

5. Create the ineterface conf file `/etc/wireguard/wg0.conf` and fill paste content below:
```
[Interface]
PrivateKey = <YOUR_PRIVATE_KEY_CREATED_ABOVE_GOES_HERE>
Address = 10.0.0.1/32
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```
* Start Wireguard server ont he interface you just created!
```
wg-quick up wg0
```
#### Note
If you want the `wg0` interface to be active on boot you need to run
`systemctl enable wg-quick@wg0`

Then you can use to `systemctl start wg-quick@wg0` start the server, `systemctl stop wg-quick@wg0` stop the server and `systemctl status wg-quick@wg0` to check the status.


### Client side setup (your node)

Repeat steps 1,3,4 and 5 except your `/etc/wireguard/wg0.conf` file should look like:

```
[Interface]
PrivateKey = <YOUR_PRIVATE_KEY_YOU_CREATED_ON_THIS_HOST>
Address= 10.0.0.2/24

[Peer]
PublicKey = <YOUR_ZAP_SERVER_PUBKEY_FROM_ABOVE>
Endpoint = <YOU_ZAP_SERVER_PUBLIC_IP>:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```


#### Validation

If setup correctly you should be able to ping through the VPN tunnel.

For example, run from the client:

```
root@raspberrypi:/etc/wireguard# ping 10.0.0.2
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.103 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.120 ms
^C
--- 10.0.0.2 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3057ms
```


The command `wg show` should have output like below when run from the client:

```
interface: wg0
  public key: <YOUR_PUBLIC_KEY>
  private key: (hidden)
  listening port: 51820

peer: <YOUR_WIREGUARD_SERVER_PUBKEY>
  endpoint: <YOUR_CLIENT_HOST_PUBLIC_IP>:51640 #Port is ephemeral on client 
  allowed ips: 10.0.0.2/24
  latest handshake: 24 seconds ago
  transfer: 180 B received, 124 B sent
  persistent keepalive: every 25 seconds
```