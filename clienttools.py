#!/usr/bin/env python3
"""
@summary: tools to talk to an Ethereum client node 

@version: v17 (19/June/2018)
@since:   19/June/2018
@organization: electron.org.uk
@author:  https://github.com/drandreaskrueger
@see: https://gitlab.com/electronDLT/chainhammer for updates
"""


################
## Dependencies:

try:
    from web3 import Web3, HTTPProvider # pip3 install web3
except:
    print ("Dependencies unavailable. Start virtualenv first!")
    exit()

from config import RPCaddress, PASSPHRASE_FILE
from clienttype import clientType


################
## Tools:


def printVersions():
    import sys
    from web3 import __version__ as web3version 
    from solc import get_solc_version
    from testrpc import __version__ as ethtestrpcversion
    
    import pkg_resources
    pysolcversion = pkg_resources.get_distribution("py-solc").version
    
    print ("versions: web3 %s, py-solc: %s, solc %s, testrpc %s, python %s" % (web3version, pysolcversion, get_solc_version(), ethtestrpcversion, sys.version.replace("\n", "")))



def start_web3connection(RPCaddress=None, account=None):
    """
    get a web3 object, and make it global 
    """
    global w3
    if RPCaddress:
        # HTTP provider 
        # (TODO: also try whether IPC provider is faster, when quorum-outside-vagrant starts working)
        w3 = Web3(HTTPProvider(RPCaddress, request_kwargs={'timeout': 120}))
    else:
        w3 = Web3(Web3.TestRPCProvider()) 
    
    print ("web3 connection established, blockNumber =", w3.eth.blockNumber, end=", ")
    print ("node version string = ", w3.version.node)
    accountname="chosen"
    if not account:
        w3.eth.defaultAccount = w3.eth.accounts[0] # set first account as sender
        accountname="first"
    print (accountname + " account of node is", w3.eth.defaultAccount, end=", ")
    print ("balance is %s Ether" % w3.fromWei(w3.eth.getBalance(w3.eth.defaultAccount), "ether"))
    
    return w3


def unlockAccount(duration=3600, account=None):
    """
    unlock once, then leave open, to later not loose time for unlocking
    """
    
    if "TestRPC" in w3.version.node:
        return True # TestRPC does not need unlocking 
    
    if not account:
        account = w3.eth.defaultAccount

    if NODENAME=="Quorum":
        passphrase=""
    else:
        with open(PASSPHRASE_FILE, "r") as f:
            passphrase=f.read().strip()

    if NODETYPE=="Parity":
        duration = w3.toHex(duration)

    return w3.personal.unlockAccount(account=account, 
                                     passphrase=passphrase,  
                                     duration=duration)


def setGlobalVariables_clientType(w3):
    """
    Set global variables.
    And if it's a Quorum PoA node, apply bugfix 
    """
    global NODENAME, NODETYPE, CONSENSUS, CHAINNAME
    NODENAME, NODETYPE, CONSENSUS, CHAINNAME = clientType(w3)
    
    print ("nodeName: %s, nodeType: %s, consensus: %s, chainName: %s" % (NODENAME, NODETYPE, CONSENSUS, CHAINNAME))
    
    return NODENAME, NODETYPE, CONSENSUS, CHAINNAME # for when imported into other modules


def if_quorum_then_bugfix(w3, NODENAME):
    """
    bugfix for quorum web3.py problem, see
    # https://github.com/ethereum/web3.py/issues/898#issuecomment-396701172
    """
    if NODENAME == "Quorum":
        from web3.middleware import geth_poa_middleware
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_stack.inject(geth_poa_middleware, layer=0)


def web3connection(RPCaddress=RPCaddress, account=None):
    """
    prints dependency versions, starts web3 connection, identifies client node type, if quorum then bugfix
    """
    
    printVersions()
    
    w3 = start_web3connection(RPCaddress=RPCaddress, account=account) 

    NODENAME, NODETYPE, CONSENSUS, CHAINNAME = setGlobalVariables_clientType(w3)

    if_quorum_then_bugfix(w3, NODENAME)
    
    return w3, NODENAME, NODETYPE, CONSENSUS, CHAINNAME


if __name__ == '__main__':
    answer = web3connection(RPCaddress=RPCaddress, account=None)
    global w3, NODENAME, NODETYPE, CONSENSUS, CHAINNAME
    w3, NODENAME, NODETYPE, CONSENSUS, CHAINNAME = answer


    