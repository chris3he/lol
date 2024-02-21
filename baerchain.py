import requests,logging,sys
from web3 import Web3
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [ %(message)s ]')

w3 = Web3(Web3.HTTPProvider('https://artio.rpc.berachain.com'))

BERA="0x0000000000000000000000000000000000000000"
WBERA ="0x5806E416dA447b267cEA759358cF22Cc41FAE80F"
HONEY="0x7EeCA4205fF31f947EdBd49195a7A88E6A91161B"
STGUSDC="0x6581e59A1C8dA66eD0D313a0d4029DcE2F746Cc5"
WETH="0x8239FBb3e3D0C2cDFd7888D8aF7701240Ac4DcA4"
WBTC="0x9DAD8A1F64692adeB74ACa26129e0F16897fF4BB"

address=""
privateKey=""
two_captcha_api_key = ''

def get_user_agent():
    from fake_useragent import UserAgent
    ua = UserAgent(browsers=["chrome","firefox"])
    return ua.random

def init(token, amount, spender, approve_all=False, main_token=BERA):
  abi=[
    {
        "inputs":[
            {
                "internalType":"address",
                "name":"",
                "type":"address"
            }
        ],
        "name":"balanceOf",
        "outputs":[
            {
                "internalType":"uint256",
                "name":"",
                "type":"uint256"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "inputs":[
            {
                "internalType":"address",
                "name":"spender",
                "type":"address"
            },
            {
                "internalType":"uint256",
                "name":"amount",
                "type":"uint256"
            }
        ],
        "name":"approve",
        "outputs":[
            {
                "internalType":"bool",
                "name":"",
                "type":"bool"
            }
        ],
        "stateMutability":"nonpayable",
        "type":"function"
    },
    {
        "inputs":[
            {
                "internalType":"address",
                "name":"",
                "type":"address"
            },
            {
                "internalType":"address",
                "name":"",
                "type":"address"
            }
        ],
        "name":"allowance",
        "outputs":[
            {
                "internalType":"uint256",
                "name":"",
                "type":"uint256"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },
    {
        "inputs":[

        ],
        "name":"decimals",
        "outputs":[
            {
                "internalType":"uint8",
                "name":"",
                "type":"uint8"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    }
]
  if token == main_token:
    amount= int(amount * 10 ** 18)
    balanceOf=w3.eth.get_balance(address)
  else:
    swapContract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=abi)
    decimals=swapContract.functions.decimals().call()
    amount= int(amount * 10 ** decimals)
    balanceOf=swapContract.functions.balanceOf(address).call()
  if amount > balanceOf:
    logging.error("Insufficient balance!")
    sys.exit(1)
  if token != main_token:
    r = swapContract.functions.allowance(address,spender).call()
    if amount > r:
      build_tx=swapContract.functions.approve(spender, amount).build_transaction({
        "nonce": w3.eth.get_transaction_count(address)
      })
      if approve_all:
        build_tx["data"]=build_tx["data"][:-64] + "f" * 64
      signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
      tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
      logging.info("Approve %s to %s, Hash: %s",token, spender, Web3.to_hex(tx_hash))
  return amount

def getFaucet(api_key,address):
  # https://github.com/2captcha/2captcha-python
  from twocaptcha import TwoCaptcha
  solver = TwoCaptcha(api_key)
  result = solver.turnstile(sitekey='0x4AAAAAAARdAuciFArKhVwt', url='https://artio.faucet.berachain.com')

  data = params = {
    "address": address
  }
  headers={
    'authority': 'artio-80085-faucet-api-cf.berachain.com', 
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9', 
    'cache-control': 'no-cache', 
    'content-type': 'text/plain;charset=UTF-8',
    'origin': 'https://artio.faucet.berachain.com/', 
    'pragma': 'no-cache',
    'referer': 'https://artio.faucet.berachain.com/',
    'user-agent': get_user_agent(),
    "Authorization": "Bearer " + result["code"]
  }
  r = requests.post(headers=headers, json=data, params=params, url="https://artio-80085-faucet-api-cf.berachain.com/api/claim")
  print(r.text)

def get_faucet_for_quicknode(api_key,address):
  from twocaptcha import TwoCaptcha
  url="https://faucet.quicknode.com/berachain/artio"
  params = {
    "_data": "root"
  }
  r = requests.get(params=params, url=url)
  sitekey = r.json()["ENV"]["RECAPTCHA_PUBLIC_KEY"]
  url=r.json()["ENV"]["OIDC_ENDPOINT"]
  solver = TwoCaptcha(api_key)
  result = solver.recaptcha(sitekey=sitekey, url=url, version='v3')
  url = "https://faucet.quicknode.com/berachain/artio"
  params={
    "_data": "routes/$"
  }
  data={
    "chain": "berachain",
    "network": "artio",
    "wallet": address,
    "recaptchaToken": result["code"],
    "visitorId": "c92103b459e94d9a27051826d837fec8",
    "_action": "step-two-skip"
  }
  r = requests.post(url=url,params=params,data=data)
  print(r.text)

# https://artio.bex.berachain.com
def bex_swap(from_token,to_token,amount_in):
  spender="0x0000000000000000000000000000000000696969"
  amount = init(token=from_token, amount=amount_in, spender=spender)
  abi=[{
        "inputs":[
            {
                "internalType":"enum IERC20DexModule.SwapKind",
                "name":"kind",
                "type":"uint8"
            },
            {
                "components":[
                    {
                        "internalType":"address",
                        "name":"poolId",
                        "type":"address"
                    },
                    {
                        "internalType":"address",
                        "name":"assetIn",
                        "type":"address"
                    },
                    {
                        "internalType":"uint256",
                        "name":"amountIn",
                        "type":"uint256"
                    },
                    {
                        "internalType":"address",
                        "name":"assetOut",
                        "type":"address"
                    },
                    {
                        "internalType":"uint256",
                        "name":"amountOut",
                        "type":"uint256"
                    },
                    {
                        "internalType":"bytes",
                        "name":"userData",
                        "type":"bytes"
                    }
                ],
                "internalType":"struct IERC20DexModule.BatchSwapStep[]",
                "name":"swaps",
                "type":"tuple[]"
            },
            {
                "internalType":"uint256",
                "name":"deadline",
                "type":"uint256"
            }
        ],
        "name":"batchSwap",
        "outputs":[
            {
                "internalType":"address[]",
                "name":"assets",
                "type":"address[]"
            },
            {
                "internalType":"uint256[]",
                "name":"amounts",
                "type":"uint256[]"
            }
        ],
        "stateMutability":"payable",
        "type":"function"
    }]
  url="https://artio-80085-dex-router.berachain.com/dex/route"
  if from_token == BERA:
    from_token=WBERA
  params={
    "quoteAsset": from_token,
    "baseAsset": to_token,
    "amount": amount,
    "swap_type": "given_in"
  }
  r = requests.get(url, params)
  swap_data=[]
  for i in r.json()["steps"]:
    data=(
      Web3.to_checksum_address(i["pool"]),
      Web3.to_checksum_address(i["assetIn"]),
      int(i["amountIn"]),
      Web3.to_checksum_address(i["assetOut"]),
      int(i["amountOut"]),
      bytes()
    )
    swap_data.append(data)
  # print(swap_data)
  contract="0x0d5862FDbdd12490f9b4De54c236cff63B038074"
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  build_tx=swapContract.functions.batchSwap(
    0,
    swap_data,
    99999999
  ).build_transaction({
      "from": address,
      # "type": 2,
      # "maxFeePerGas": w3.to_wei(10240, 'gwei'),
      # "maxPriorityFeePerGas": w3.eth.max_priority_fee * 2,
      "gasPrice": w3.eth.gas_price * 3,
      "nonce": w3.eth.get_transaction_count(address)
  })
  # build_tx["gas"]=w3.eth.estimate_gas(build_tx)
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Swap %s to %s, Hash: %s",from_token, to_token, Web3.to_hex(tx_hash))
def bex_pool():
  spender="0x0000000000000000000000000000000000696969"
  amount = init(token=WBTC, amount=0.00035, spender=spender)

# https://artio.honey.berachain.com
def honey_mint(token, amount):
  contract="0x09ec711b81cD27A6466EC40960F2f8D85BB129D9"
  amount = init(token=token, amount=amount, spender=contract)
  
  abi=[{
        "type":"function",
        "name":"mint",
        "inputs":[
            {
                "name":"asset",
                "type":"address",
                "internalType":"address"
            },
            {
                "name":"receiver",
                "type":"address",
                "internalType":"address"
            },
            {
                "name":"amount",
                "type":"uint256",
                "internalType":"uint256"
            }
        ],
        "outputs":[
            {
                "name":"",
                "type":"uint256",
                "internalType":"uint256"
            }
        ],
        "stateMutability":"nonpayable"
    }]
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  build_tx= swapContract.functions.mint(
    address,
    STGUSDC,
    amount
  ).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Minted HONEY, Hash: %s", Web3.to_hex(tx_hash))
def honey_redeem(amount, token=HONEY):
  contract="0x09ec711b81cD27A6466EC40960F2f8D85BB129D9"
  amount=init(token=token, amount=amount, spender=contract)

  abi=[{
    "type": "function",
    "name": "redeem",
    "inputs": [{
        "name": "asset",
        "type": "address",
        "internalType": "address"
    }, {
        "name": "honeyAmount",
        "type": "uint256",
        "internalType": "uint256"
    }, {
        "name": "receiver",
        "type": "address",
        "internalType": "address"
    }],
    "outputs": [{
        "name": "",
        "type": "uint256",
        "internalType": "uint256"
    }],
    "stateMutability": "nonpayable"
}]
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  build_tx= swapContract.functions.redeem(
    address,
    amount,
    STGUSDC
  ).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Redeem STGUSDC, Hash: %s", Web3.to_hex(tx_hash))

# https://artio.bend.berachain.com
def bend_supply(token, amount):
  contract="0x9261b5891d3556e829579964B38fe706D0A2D04a"
  amount = init(token=token, amount=amount, spender=contract)
  abi=[{
            "inputs": [{
                "internalType": "address",
                "name": "asset",
                "type": "address"
            }, {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }, {
                "internalType": "address",
                "name": "onBehalfOf",
                "type": "address"
            }, {
                "internalType": "uint16",
                "name": "referralCode",
                "type": "uint16"
            }],
            "name": "supply",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  build_tx=swapContract.functions.supply(
    token,
    amount,
    address,
    0
  ).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Supply %s, Hash: %s", token, Web3.to_hex(tx_hash))
def bend_withdraw(token, amount=None):
  abi=[
        {
        "inputs":[

        ],
        "name":"decimals",
        "outputs":[
            {
                "internalType":"uint8",
                "name":"",
                "type":"uint8"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    }
  ]
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=abi)
  decimals=swapContract.functions.decimals().call()
  amount= int(amount * 10 ** decimals)
  contract="0x9261b5891d3556e829579964B38fe706D0A2D04a"
  abi=[{
        "inputs":[
            {
                "internalType":"address",
                "name":"",
                "type":"address"
            }
        ],
        "name":"balanceOf",
        "outputs":[
            {
                "internalType":"uint256",
                "name":"",
                "type":"uint256"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },{
            "inputs": [{
                "internalType": "address",
                "name": "asset",
                "type": "address"
            }, {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }, {
                "internalType": "address",
                "name": "to",
                "type": "address"
            }],
            "name": "withdraw",
            "outputs": [{
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
  
  if token == WBTC:
    aToken="0x6070AB34ECCD909f7C2ab8fd920Ff0eB1FCab185"
  elif token == WETH:
    aToken=""
  elif token == HONEY:
    aToken=""
  swapContract = w3.eth.contract(aToken, abi=abi)
  max_amount=swapContract.functions.balanceOf(address).call()
  if not amount or amount > max_amount:
    amount = max_amount
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  build_tx = swapContract.functions.withdraw(
    token,
    amount,
    address
  ).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Withdraw %s, Hash: %s", token, Web3.to_hex(tx_hash))
def bend_borrow(address,amount,token=HONEY):
  abi=[{
        "inputs":[

        ],
        "name":"decimals",
        "outputs":[
            {
                "internalType":"uint8",
                "name":"",
                "type":"uint8"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },{
            "inputs": [{
                "internalType": "address",
                "name": "asset",
                "type": "address"
            }, {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }, {
                "internalType": "uint256",
                "name": "interestRateMode",
                "type": "uint256"
            }, {
                "internalType": "uint16",
                "name": "referralCode",
                "type": "uint16"
            }, {
                "internalType": "address",
                "name": "onBehalfOf",
                "type": "address"
            }],
            "name": "borrow",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }]
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=abi)
  decimals=swapContract.functions.decimals().call()
  amount= int(amount * 10 ** decimals)
  contract="0x9261b5891d3556e829579964B38fe706D0A2D04a"
  swapContract = w3.eth.contract(contract, abi=abi)
  build_tx=swapContract.functions.borrow(token,amount,2,0,address).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Borrow %s, Hash: %s", token, Web3.to_hex(tx_hash))
def bend_repay(address,amount=None,token=HONEY):
  contract="0x9261b5891d3556e829579964B38fe706D0A2D04a"
  init(token=token, amount=amount, spender=contract)
  abi=[{
        "inputs":[

        ],
        "name":"decimals",
        "outputs":[
            {
                "internalType":"uint8",
                "name":"",
                "type":"uint8"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },{
        "inputs":[
            {
                "internalType":"address",
                "name":"",
                "type":"address"
            }
        ],
        "name":"balanceOf",
        "outputs":[
            {
                "internalType":"uint256",
                "name":"",
                "type":"uint256"
            }
        ],
        "stateMutability":"view",
        "type":"function"
    },{
    "inputs": [{
        "internalType": "address",
        "name": "asset",
        "type": "address"
    }, {
        "internalType": "uint256",
        "name": "amount",
        "type": "uint256"
    }, {
        "internalType": "uint256",
        "name": "interestRateMode",
        "type": "uint256"
    }, {
        "internalType": "address",
        "name": "onBehalfOf",
        "type": "address"
    }],
    "name": "repay",
    "outputs": [{
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
    }],
    "stateMutability": "nonpayable",
    "type": "function"
}]
  swapContract = w3.eth.contract(token, abi=abi)
  decimals=swapContract.functions.decimals().call()
  amount= int(amount * 10 ** decimals)
  vdHONEY="0x7f8E75356015fECfafF66e2B34F181A093Dc4519"
  swapContract = w3.eth.contract(vdHONEY, abi=abi)
  max_amount=swapContract.functions.balanceOf(address).call()
  if not amount or amount > max_amount:
    amount = max_amount
  swapContract = w3.eth.contract(contract, abi=abi)
  build_tx=swapContract.functions.repay(token,amount,2,address).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  signed_tx = w3.eth.account.sign_transaction(build_tx, privateKey)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  logging.info("Repay %s, Hash: %s", token, Web3.to_hex(tx_hash))


def beranames(name=None, years=1):
  if not name:
    import random,string
    name=''.join(random.sample(string.ascii_letters + string.digits, 8)).lower()
  abi=[{
    "stateMutability": "payable",
    "type": "function",
    "inputs": [{
        "name": "chars",
        "internalType": "string[]",
        "type": "string[]"
    }, {
        "name": "duration",
        "internalType": "uint256",
        "type": "uint256"
    }, {
        "name": "whois",
        "internalType": "address",
        "type": "address"
    }, {
        "name": "metadataURI",
        "internalType": "string",
        "type": "string"
    }, {
        "name": "to",
        "internalType": "address",
        "type": "address"
    }],
    "name": "mintNative",
    "outputs": [{
        "name": "",
        "internalType": "uint256",
        "type": "uint256"
    }]
  }]
  contract="0x8D20B92B4163140F413AA52A4106fF9490bf2122"
  swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  metadataURI="https://beranames.com/api/metadata/69"
  build_tx=swapContract.functions.mintNative(list(name), years, address, metadataURI, address).build_transaction({
    "from": address,
    "nonce": w3.eth.get_transaction_count(address)
  })
  print(build_tx)
  abi=[{
    "inputs": [{
        "components": [{
            "name": "target",
            "type": "address"
        }, {
            "name": "allowFailure",
            "type": "bool"
        }, {
            "name": "callData",
            "type": "bytes"
        }],
        "name": "calls",
        "type": "tuple[]"
    }],
    "name": "aggregate3",
    "outputs": [{
        "components": [{
            "name": "success",
            "type": "bool"
        }, {
            "name": "returnData",
            "type": "bytes"
        }],
        "name": "returnData",
        "type": "tuple[]"
    }],
    "stateMutability": "view",
    "type": "function"
}]
  # contract="0x9d1dB8253105b007DDDE65Ce262f701814B91125"
  # data="0x82ad56cb00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000064f412f821086253204645174c456b7532ba45270000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000e49ac64e4d0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000017000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008d20b92b4163140f413aa52a4106ff9490bf21220000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000248ccc5f80dcac8b688033717a608cd411e95c40bd20977b792b034c75d6d2893213fa3c2f00000000000000000000000000000000000000000000000000000000"
  # swapContract = w3.eth.contract(address=Web3.to_checksum_address(contract), abi=abi)
  # _,r=swapContract.decode_function_input(data)
  # r=r["calls"][0]["callData"]
  # print(swapContract.decode_function_input(w3.to_hex(r)))
# getFaucet(address=address,api_key=two_captcha_api_key)
# get_faucet_for_quicknode(address=address,api_key=two_captcha_api_key)

# bex_swap(from_token=BERA,to_token=HONEY, amount_in=0.01)

# 目前项目方只支持STGUSDC和HONEY
# honey_mint(token=STGUSDC, amount=0.1)
# honey_redeem(amount=1)

bend_supply(token=HONEY, amount=1)
# bend_withdraw(token=HONEY)

# beranames()
# bex_pool()

# bend_borrow(address, amount=3)
# bend_repay(address, amount=10)
