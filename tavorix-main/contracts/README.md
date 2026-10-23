# Tavorix contracts (draft, UNAUDITED)

Setup: `forge init --no-commit && forge install OpenZeppelin/openzeppelin-contracts@v5.0.2`

## Contracts
- TavorixToken: fixed 510M supply, no mint/owner/pause, Permit + Votes, burn floor 400M.
- VestingVault: funded-upfront, non-revocable schedules (TGE + cliff + linear), sealable.

## Planned distribution (constructor recipients)
Presale vesting, liquidity (to LP locker), team vesting, ecosystem, airdrop, treasury multisig.
Amounts must sum to 510,000,000e18 or deployment reverts.

## Required before mainnet
1. Foundry unit + fuzz tests, and invariants:
   - sum(claimed) + vault balance >= totalOwed at all times
   - claimable never exceeds total; claimed monotonic
   - totalSupply >= 400M forever; no function increases supply after deploy
2. Static analysis (Slither), coverage >95% on these files.
3. Independent audit, then bug bounty.
4. Deploy from a multisig; verify on BscScan; publish addresses and lock proofs.
5. Test on BNB Smart Chain testnet (Chapel) first.

DO NOT deploy with real funds before an independent audit. This code has not been compiled or tested here.

## PresaleVault (BNB Smart Chain, USDT 18 decimals)
- Price 0.0009 USDT, hard cap 135,000 USDT, Merkle allowlist (leaf = keccak(abi.encode(wallet, maxUSDT))).
- finalize(): 60% USDT + 60% of tokens sold -> PancakeSwap v2 pool at presale price; 40% USDT -> dev wallet;
  LP locked 24 months in this contract, then released to treasury; unsold tokens -> treasury.
- Buyers: 15% at finalize, 85% linear over 270 days. Refund if soft cap fails or finalize stuck 30 days.
- Deploy params to decide: softCap, minBuy, maxPerWallet, start/end, factory address (take from official
  PancakeSwap docs and verify on BscScan), USDT address (official BSC-USD), treasury, devWallet, admin.
- Needs BSC mainnet fork tests (pool creation, skim donation attack, rounding, vesting, refunds).
