import hashlib
import json
import logging
import secp256k1
import time
from websocket import create_connection


class NostpyClient:
    def __init__(self, relays, pubkey, privkey, nostr_event, response) -> None:
        self.relays = relays
        self.pubkey = pubkey
        self.privkey = privkey
        self.kind9734 = nostr_event
        self.created_at = response["settle_date"]
        self.zap_reciept_tags = [
            ["description", json.dumps(nostr_event)],
            ["bolt11", response["payment_request"]],
            ["preimage", response["r_preimage"]],
        ]

    def sign_event_id(self, event_id: str, private_key_hex: str) -> str:
        private_key = secp256k1.PrivateKey(bytes.fromhex(private_key_hex))
        sig = private_key.schnorr_sign(
            bytes.fromhex(event_id), bip340tag=None, raw=True
        )
        return sig.hex()

    def calc_event_id(
        self,
        public_key: str,
        created_at: int,
        kind_number: int,
        tags: list,
        content: str,
    ) -> str:
        data = [0, public_key, created_at, kind_number, tags, content]
        data_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(data_str.encode("UTF-8")).hexdigest()

    def parse_tags(self, logger):
        try:
            tag_list = [tag_pair for tag_pair in self.kind9734["tags"]]
            for tag in self.zap_reciept_tags:    
                tag_list.append(tag)
            return tag_list
        except Exception as exc:
            logger.error(f"Error parsing kind 9735 tags: {exc}")

    def create_event(self, kind_number, logger):
        kind_9735_tags = self.parse_tags(logger)
        #content = ""
        event_id = self.calc_event_id(
            self.pubkey, self.created_at, kind_number, kind_9735_tags, content=""
        )
        signature_hex = self.sign_event_id(event_id, self.privkey)
        event_data = {
            "id": event_id,
            "pubkey": self.pubkey,
            "kind": kind_number,
            "created_at": self.created_at,
            "tags": kind_9735_tags,
            "content": '',#content,
            "sig": signature_hex,
        }
        return event_data

    def verify_signature(self, event_id: str, pubkey: str, sig: str, logger) -> bool:
        try:
            pub_key = secp256k1.PublicKey(bytes.fromhex("02" + pubkey), True)
            result = pub_key.schnorr_verify(
                bytes.fromhex(event_id), bytes.fromhex(sig), None, raw=True
            )
            if result:
                logger.info(f"Verification successful for event: {event_id}")
            else:
                logger.error(f"Verification failed for event: {event_id}")
            return result
        except (ValueError, TypeError) as e:
            logger.error(f"Error verifying signature for event {event_id}: {e}")
            return False

    def send_event(self, ws_relay, logger):
        try:
            ws = create_connection(ws_relay)
            logger.info(f"WebSocket connection created with {ws_relay}")
            event_data = self.create_event(9735, logger)
            signature_valid = self.verify_signature(event_data["id"], self.pubkey, event_data["sig"], logger)
            if signature_valid:
                json_event = json.dumps(("EVENT", event_data))
                ws.send(json_event)
                logger.debug(f"Event sent to {ws_relay}: {json_event}")
            else:
                logger.error("Invalid signature, event not sent.")
            ws.close()
            logger.info("WebSocket connection closed.")
        except Exception as exc:
            logger.error(f"Error sending ws event: {exc}")
