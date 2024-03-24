import json
import logging
import os
import socket
import time

import requests
import socks
from dotenv import load_dotenv
from ddtrace import tracer, patch_all
from nostr import NostpyClient
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
HEX_PRIV_KEY = os.getenv("HEX_PRIV_KEY")
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
    
def check_invoice_payment(payment_request, max_attempts=10, sleep_time=5):
    """
    Check if the specified invoice has been paid.

    Parameters:
    - payment_request (str): The payment request of the invoice.
    - max_attempts (int): The maximum number of attempts to check the payment.
    - sleep_time (int): The time to sleep between each attempt.

    Returns:
    - bool: True if the invoice has been paid, False otherwise.
    """
    try:
        attempts = 0
        while attempts < max_attempts:
            # Check payment status using LND REST interface over Tor
            url = f"https://{VPN_HOST}:{LND_REST_PORT}/v1/invoice/{payment_request}"
            logger.debug(f"Sending request to {url}")
            response = requests.get(
                url,
                headers={"Grpc-Metadata-macaroon": LND_INVOICE_MACAROON_HEX},
                verify=False,
            )
            response.raise_for_status()
            logger.debug(f"Check Payment response is: {response}")
            invoice_status = response.json()["settled"]
            if invoice_status:
                logger.info("Invoice has been paid successfully.")
                return True
            else:
                logger.debug("Invoice not yet paid. Retrying...")
            attempts += 1
            time.sleep(sleep_time)

        logger.warning("Maximum attempts reached. Invoice may not have been paid.")
        return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking invoice payment: {e}")
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
            nostr_event = json.loads(nostr_resp)
            description = nostr_event["content"]
            tags = nostr_event["tags"]
            relays_value = next((item[1:] for item in tags if item[0] == 'relays'), [])
            logger.debug(f"Relays are: {relays_value} and of type {type(relays_value)}")

        


        # Generate an invoice
        payment_request = get_invoice(amount_millisatoshis, description)
        logger.debug(f"Payment request is: {payment_request}")

        check = check_invoice_payment(payment_request=payment_request)
        logger.debug(f"Line after check inv")
        if check:
            lnurl_obj = NostpyClient(relays_value, HEX_PUBKEY, HEX_PRIV_KEY)
            for relay in lnurl_obj.relays:
                lnurl_obj.send_event(relay, logger)
                logger.debug(f"Event sent is {relay}")

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
