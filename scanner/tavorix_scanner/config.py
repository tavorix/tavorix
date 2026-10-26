"""Chain constants for BNB Smart Chain mainnet (chain id 56).
VERIFY every address against official docs / BscScan before relying on it."""
WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2de08d9173bc095c"
USDT = "0x55d398326f99059fF775485246999027B3197955"  # BSC-USD (18 decimals); VERIFY
PANCAKE_V2_FACTORY = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
DEAD_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}
# Famous tokens that scammers copy. Use ONLY official BSC addresses you verified on BscScan, then add more here.
KNOWN_TOKENS = {
    "USDT": {"address": USDT, "names": ["Tether USD", "Tether"]},
    "WBNB": {"address": WBNB, "names": ["Wrapped BNB"]},
}
# Add addresses of LP locker contracts you trust (verify each one yourself).
LP_LOCKER_ADDRESSES: set = set()

# Function selectors (4 bytes). Double-check any selector with a keccak tool before trusting it.
SELECTORS = {
    "mint": ["40c10f19", "a0712d68"],          # mint(address,uint256), mint(uint256)
    "blacklist": ["f9f92be4", "fe575a87"],     # blacklist(address), isBlacklisted(address)
    "pause": ["8456cb59"],                     # pause()
    "proxy": ["5c60da1b"],                     # implementation()
}
EIP1967_IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
