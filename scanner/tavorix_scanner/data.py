from .models import TokenData


def fetch_token_data(address: str) -> TokenData:
    """TODO: fill TokenData from real sources. Run this on your own machine (needs network):
    - BNB Chain RPC node: bytecode, owner(), total supply, holder balances, LP pair reserves
    - BscScan API: verified source code (scan ABI/source for mint, blacklist, pause, tax setters, proxy)
    - Local fork (Foundry/Anvil): simulate buy then sell to detect honeypots and measure tax
    - LP locker contracts: locked percentage and unlock time
    - Deployer history: earlier tokens by the same deployer that were labeled scams
    """
    raise NotImplementedError("Implement data fetching; see docstring.")
