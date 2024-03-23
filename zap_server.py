import json
import logging
import os
import socket

import requests
import socks
from dotenv import load_dotenv
from flask import Flask, jsonify, request


app = Flask(__name__)

load_dotenv()

LND_ONION_ADDRESS = os.getenv("LND_ONION_ADDRESS")
LND_TOR_PORT = int(os.getenv("LND_TOR_PORT"))
LND_INVOICE_MACAROON_HEX = os.getenv("LND_INVOICE_MACAROON_HEX")
INTERNET_IDENTIFIER = os.getenv("INTERNET_IDENTIFIER")
HEX_PUBKEY = os.getenv("HEX_PUBKEY")
DOMAIN = os.getenv("DOMAIN")
identity = INTERNET_IDENTIFIER.split("@")[0]


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_invoice(amount, description):
    try:
        # Create an invoice using LND REST interface over Tor with macaroon authentication
        with socks.socksocket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)  # Tor SOCKS proxy
            s.connect((LND_ONION_ADDRESS, LND_TOR_PORT))
            url = f"https://{LND_ONION_ADDRESS}:{LND_TOR_PORT}/v1/invoices"
            logger.debug(f"Sending request to {url}")
            response = requests.post(
                url,
                json={"value": amount, "memo": description},
                headers={"Grpc-Metadata-macaroon": LND_INVOICE_MACAROON_HEX},
                proxies={
                    "http": "socks5h://127.0.0.1:9050",
                    "https": "socks5h://127.0.0.1:9050",
                },
                verify=False,
            )
            response.raise_for_status()
            logger.debug(f"Get Invoice response is: {response}")
        invoice_data = response.json()
        logger.debug(f"Received invoice data: {invoice_data}")
        return invoice_data["payment_request"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating invoice: {e}")
        logger.debug(
            f"Response content: {response.content if 'response' in locals() else None}"
        )
        raise


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


@app.route(f"/.well-known/lnurlp/{identity}", methods=["GET"])
def lnurl_response():
    max_sendable = 500000000  # Replace with the actual maximum amount in millisats
    min_sendable = 1000  # Replace with the actual minimum amount in millisats
    metadata = f'{{"text/identifier": "{identity}@{DOMAIN}"}}'
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
    app.run(debug=True)
