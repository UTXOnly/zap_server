import hashlib
import json
import logging
import secp256k1
import time
import websockets


class NostpyClient:
    def __init__(self, relays, pubkey, privkey, nostr_event, response) -> None:
        self.relays = relays
        self.pubkey = pubkey
        self.privkey = privkey
        self.kind9734 = nostr_event
        #self.created_at = response['settle_date']
        #self.bolt11 = response['payment_request']
        #self.preimage = response['r_preimage']
        self.response = response
        self.zap_reciept_tags = ['settle_date', 'payment_request', 'r_preimage']
        

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
            tag_list = [tag_pair for tag_pair in self.kind9734['tags']]
            for key in self.zap_reciept_tags:
                logger.debug(f"Adding {[key, self.response[key]]} of type {type([key, key[key]])}")
                tag_list.append([key, key[key]])
            return tag_list
        except Exception as exc:
            logger.error(f"Error parsing kind 9375 tags: {exc}")


    def create_event(self, kind_number, logger):
        
        kind_9375_tags = self.parse_tags(logger)
        created_at = int(time.time())
        kind_number = 9374
        content = ''
        event_id = self.calc_event_id(
            self.pubkey, created_at, kind_number, kind_9375_tags, content
        )
        signature_hex = self.sign_event_id(event_id, self.privkey)
        event_data = {
            "id": event_id,  # event_id,
            "pubkey": self.pubkey,
            "kind": kind_number,
            "created_at": self.created_at,
            "tags": kind_9375_tags,
            "content": content,
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
        logger.debug("Inside send event func")
        with websockets.connect(ws_relay) as ws:
            logger.info("WebSocket connection created.")

            event_data = self.create_event(9375, logger)
            sig = event_data['sig']
            id = event_data['id']
            signature_valid = self.verify_signature(id, self.pubkey, sig, logger)
            if signature_valid:
                event_json = json.dumps(("EVENT", event_data))
                ws.send(event_json)
                logger.info(f"Event sent: {event_json}")
            else:
                logger.error("Invalid signature, event not sent.")
            logger.info("WebSocket connection closed.")


    #def query(self, ws_relay, logger):
    #    with websockets.connect(ws_relay) as ws:
    #        logger.info("WebSocket connection created.")
#
    #        current_time = int(time.time())  # Get the current timestamp
    #        past_time = current_time - 120  # Subtract 180 seconds (3 minutes)
#
    #        query_dict = {
    #            # "search": "specialsearch",
    #            "kinds": [1, 7, 9735, 30023],
    #            "limit": 300,
    #            "since": past_time,
    #            # "#e": ["96acd33c59abb33dc467d5528536ced2983827efcba89c84343aa3e78d8d44ea"],
    #            "authors": [
    #                "b97b26c3ec44390727b5800598a9de42b222ae7b5402abcf13d2ae8f386e4e0c",
    #                "d576043ce19fa2cb684de60ffb8fe529e420a1411b96b6788f11cb0442252eea",
    #            ],
    #        }
#
    #        q = query_dict
    #        query_ws = json.dumps(("REQ", "5326483051590112", q))
    #        for i in range(5):
    #            ws.send(query_ws)
    #            logger.info(f"Query sent: {query_ws}")
    #            response = ws.recv()
    #            logger.info(f"Response from websocket server: {response}")

if __name__ == "__main__":
    pass
