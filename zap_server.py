import json
import logging
import os
import socket

import requests
import socks
from dotenv import load_dotenv
from ddtrace import tracer, patch_all
from flask import Flask, jsonify, request


app = Flask(__name__)

load_dotenv()

tracer.configure(hostname="127.0.0.1", port=8126)
patch_all()

LND_ONION_ADDRESS = os.getenv("LND_ONION_ADDRESS")
VPN_HOST = os.getenv("VPN_HOST")
LND_REST_PORT = int(os.getenv("LND_REST_PORT"))
LND_INVOICE_MACAROON_HEX = os.getenv("LND_INVOICE_MACAROON_HEX")
INTERNET_IDENTIFIER = os.getenv("INTERNET_IDENTIFIER")
HEX_PUBKEY = os.getenv("HEX_PUBKEY")
DOMAIN = os.getenv("DOMAIN")
IDENTITY = INTERNET_IDENTIFIER.split("@")[0]

logging.basicConfig(
    filename="./zap_server.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def make_http_request(url, headers, data):
    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            verify=False,  # Disable SSL verification if needed
        )
        response.raise_for_status()
        invoice_data = response.json()
        logger.debug(f"Received invoice data: {invoice_data}")
        return invoice_data["payment_request"]
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error making HTTP request: {e}")


def get_invoice(amount, description):
    headers = {"Grpc-Metadata-macaroon": LND_INVOICE_MACAROON_HEX}
    data = {"value": amount, "memo": description}
    try:
        if LND_ONION_ADDRESS:
            # Use Tor SOCKS proxy
            s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # Tor SOCKS proxy
            s.connect((LND_ONION_ADDRESS, LND_REST_PORT))
            url = f"https://{LND_ONION_ADDRESS}:{LND_REST_PORT}/v1/invoices"
            with s:
                return make_http_request(url, headers, data)
        elif VPN_HOST:
            # Use WireGuard VPN
            url = f"https://{VPN_HOST}:{LND_REST_PORT}/v1/invoices"
            return make_http_request(url, headers, data)
        else:
            raise ValueError("Tor or VPN variables not provided.")
    except Exception as e:
        raise RuntimeError(f"Error creating invoice: {e}")


@app.route("/lnurl-pay", methods=["GET"])
def lnurl_pay():
    try:
        # Get parameters from the request or set default values
        logger.debug(f"Payload is {request}")
        amount_satoshis = int(
            request.args.get("amount", 1000)
        )  # Default to 1000 millisatoshis (1 satoshi)
        amount_millisatoshis = amount_satoshis / 1000

        description = request.args.get("comment")
        nostr_resp = request.args.get("nostr")
        if nostr_resp:
            description = json.loads(nostr_resp).get("content")
            nostr_body = json.loads(nostr_resp)
            logger.debug(f"nostr body is {nostr_body} and of type{type(nostr_body)}")

        #for item in request:
        #    logger.debug(f"item in req is")
        tags = nostr_body["tags"]
        logger.debug(f"Tags are {tags} and of type {type(tags)}")
        #loaded = json.loads(tags)
        #logger.debug(f"loaded is {loaded}")

        for item in nostr_body:
            logger.info(f"Item in nost resp is {item}")

        # Generate an invoice
        payment_request = get_invoice(amount_millisatoshis, description)
        logger.debug(f"Payment request is: {payment_request}")

        return jsonify(
            {
                "pr": payment_request,
                "successAction": {"tag": "message", "message": "LN Invoice generated"},
            }
        )

    except Exception as e:
        logger.error(f"Error generating LNURL pay: {e}")
        return jsonify({"error": str(e)}), 500


@app.route(f"/.well-known/lnurlp/{IDENTITY}", methods=["GET"])
def lnurl_response():
    max_sendable = 500000000  # Replace with the actual maximum amount in millisats
    min_sendable = 1000  # Replace with the actual minimum amount in millisats
    metadata = f'{{"text/identifier": "{IDENTITY}@{DOMAIN}"}}'
    callback_url = f"https://{DOMAIN}/lnurl-pay"

    comment_allowed = 200  # Replace with # of char allowed in comment
    allow_nostr = "true"
    nostr_pubkey = HEX_PUBKEY

    # Build the response JSON
    lnurl_pay_response = {
        "callback": callback_url,
        "maxSendable": max_sendable,
        "minSendable": min_sendable,
        "metadata": metadata,
        "commentAllowed": comment_allowed,
        "tag": "payRequest",
        "allowsNostr": allow_nostr,
        "nostrPubkey": nostr_pubkey,
    }

    return jsonify(lnurl_pay_response)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5555)
