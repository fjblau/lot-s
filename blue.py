#!/usr/bin/python

import requests

headers = {"Content-Type": "application/json", "Accept": "application/json"}

payload = {
  "jsonrpc": "2.0",
  "method": "invoke",
  "params": {
    "type": 1,
    "chaincodeID": {
      "name": "daa32b86da6e52e446e3bb01d272bc12d1d223d8651c3c96ee990af8ea08e33dcc9fdac82539ce17b8e3ce795323e5b7f22d54cb42c42da5d71d67b9cde1cfe4"
    },
    "ctorMsg": {
      "function": "write",
      "args": [
        "test_word", "here I am"
      ]
    },
    "secureContext": "user_type1_34135b9471"
  },
  "id": 0
}

r=requests.post("https://1c1390b2-5da0-4644-ac20-7414429bbb94_vp1.us.blockchain.ibm.com:443/chaincode", verify=False, headers=headers, data=payload)
r.json()
