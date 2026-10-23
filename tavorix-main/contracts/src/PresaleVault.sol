// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {MerkleProof} from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IPancakeFactory {
    function getPair(address a, address b) external view returns (address);
    function createPair(address a, address b) external returns (address);
}

interface IPancakePair {
    function getReserves() external view returns (uint112, uint112, uint32);
    function skim(address to) external;
    function mint(address to) external returns (uint256 liquidity);
}

/// @title PresaleVault
/// @notice Allowlisted USDT presale for Tavorix on BNB Smart Chain.
///  - Price fixed at 0.0009 USDT/token. Hard cap 135,000 USDT (150M tokens).
///  - On finalize, in ONE transaction: 60% of raised USDT + matching tokens seed a
///    PancakeSwap v2 pool at the presale price (listing price == presale price);
///    40% of USDT goes to the dev wallet. LP tokens stay locked in this contract 24 months.
///  - Buyers vest: 15% at finalize, remaining 85% linearly over 9 months.
///  - If soft cap fails (or finalize is stuck for 30 days) buyers can refund in full.
///  - No owner can touch buyer funds. The only admin action is setting the Merkle
///    allowlist root before the sale starts.
/// @dev BSC USDT has 18 decimals; the constructor enforces this.
contract PresaleVault is ReentrancyGuard {
    using SafeERC20 for IERC20;

    // price = PRICE_NUM / PRICE_DEN USDT per token = 0.0009
    uint256 public constant PRICE_NUM = 9;
    uint256 public constant PRICE_DEN = 10_000;
    uint256 public constant HARD_CAP = 135_000 ether;
    uint256 public constant SALE_TOKENS = 150_000_000 ether;
    uint256 public constant LP_TOKENS_MAX = 90_000_000 ether;
    uint256 public constant LP_BPS = 6_000;
    uint256 public constant TGE_BPS = 1_500;
    uint256 public constant VEST_DURATION = 270 days;
    uint256 public constant LP_LOCK = 730 days;
    uint256 public constant FINALIZE_GRACE = 30 days;

    IERC20 public immutable token;
    IERC20 public immutable usdt;
    IPancakeFactory public immutable factory;
    address public immutable treasury;
    address public immutable devWallet;
    address public immutable admin; // multisig; may only set the allowlist root before start
    uint256 public immutable startTime;
    uint256 public immutable endTime;
    uint256 public immutable softCap;
    uint256 public immutable minBuy;
    uint256 public immutable maxPerWallet;

    bytes32 public merkleRoot;
    bool public funded;
    bool public finalized;
    bool public refundsStarted;
    bool public tokensReturned;
    uint256 public raised;
    uint256 public tokensSold;
    uint256 public finalizedAt;
    address public lpPair;
    uint256 public lpUnlockTime;

    mapping(address => uint256) public contributed; // USDT
    mapping(address => uint256) public bought;      // tokens
    mapping(address => uint256) public claimed;     // tokens

    event Bought(address indexed user, uint256 usdtAmount, uint256 tokenAmount);
    event Finalized(uint256 raised, uint256 tokensSold, address pair, uint256 lpUsdt, uint256 lpTokens, uint256 lpUnlockTime);
    event Claimed(address indexed user, uint256 amount);
    event Refunded(address indexed user, uint256 amount);
    event LPReleased(address indexed to, uint256 amount);

    error ZeroAddress();
    error BadParams();
    error NotAdmin();
    error NotFunded();
    error AlreadyFunded();
    error SaleClosed();
    error BadProof();
    error LimitExceeded();
    error BelowMin();
    error CapExceeded();
    error NotFinalizable();
    error NotRefundable();
    error NothingToClaim();
    error StillLocked();
    error PoolNotEmpty();

    constructor(
        IERC20 token_,
        IERC20 usdt_,
        IPancakeFactory factory_,
        address treasury_,
        address devWallet_,
        address admin_,
        bytes32 merkleRoot_,
        uint256 startTime_,
        uint256 endTime_,
        uint256 softCap_,
        uint256 minBuy_,
        uint256 maxPerWallet_
    ) {
        if (
            address(token_) == address(0) || address(usdt_) == address(0) || address(factory_) == address(0)
                || treasury_ == address(0) || devWallet_ == address(0) || admin_ == address(0)
        ) revert ZeroAddress();
        if (IERC20Metadata(address(usdt_)).decimals() != 18) revert BadParams();
        if (
            startTime_ <= block.timestamp || endTime_ <= startTime_ || softCap_ == 0 || softCap_ > HARD_CAP
                || minBuy_ == 0 || maxPerWallet_ < minBuy_
        ) revert BadParams();

        token = token_;
        usdt = usdt_;
        factory = factory_;
        treasury = treasury_;
        devWallet = devWallet_;
        admin = admin_;
        merkleRoot = merkleRoot_;
        startTime = startTime_;
        endTime = endTime_;
        softCap = softCap_;
        minBuy = minBuy_;
        maxPerWallet = maxPerWallet_;
    }

    /// @notice Deposit the sale tokens and the LP tokens (240M Tavorix). One time.
    function fund() external {
        if (funded) revert AlreadyFunded();
        funded = true;
        token.safeTransferFrom(msg.sender, address(this), SALE_TOKENS + LP_TOKENS_MAX);
    }

    function setMerkleRoot(bytes32 root) external {
        if (msg.sender != admin) revert NotAdmin();
        if (block.timestamp >= startTime) revert SaleClosed();
        merkleRoot = root;
    }

    /// @param allocation max USDT this wallet may contribute (leaf of the KYC allowlist)
    function buy(uint256 amount, uint256 allocation, bytes32[] calldata proof) external nonReentrant {
        if (!funded) revert NotFunded();
        if (block.timestamp < startTime || block.timestamp >= endTime || finalized) revert SaleClosed();
        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encode(msg.sender, allocation))));
        if (!MerkleProof.verifyCalldata(proof, merkleRoot, leaf)) revert BadProof();

        uint256 newTotal = raised + amount;
        if (newTotal > HARD_CAP) revert CapExceeded();
        if (amount < minBuy && newTotal != HARD_CAP) revert BelowMin();

        uint256 userLimit = allocation < maxPerWallet ? allocation : maxPerWallet;
        if (contributed[msg.sender] + amount > userLimit) revert LimitExceeded();

        uint256 tokens = (amount * PRICE_DEN) / PRICE_NUM;
        contributed[msg.sender] += amount;
        bought[msg.sender] += tokens;
        raised = newTotal;
        tokensSold += tokens;

        usdt.safeTransferFrom(msg.sender, address(this), amount);
        emit Bought(msg.sender, amount, tokens);
    }

    /// @notice Anyone can finalize once the sale ended (or hard cap hit) and soft cap is met.
    function finalize() external nonReentrant {
        if (!funded || finalized || refundsStarted) revert NotFinalizable();
        if (raised < softCap) revert NotFinalizable();
        if (block.timestamp < endTime && raised < HARD_CAP) revert NotFinalizable();

        finalized = true;
        finalizedAt = block.timestamp;

        uint256 lpUsdt = (raised * LP_BPS) / 10_000;
        uint256 lpTokens = (tokensSold * LP_BPS) / 10_000;

        address pair = factory.getPair(address(token), address(usdt));
        if (pair == address(0)) pair = factory.createPair(address(token), address(usdt));
        // Tavorix did not exist outside this vault before now, so nobody can hold it:
        // only stray USDT could have been sent to the pair. Sweep it, then require an empty pool.
        IPancakePair(pair).skim(address(this));
        (uint112 r0, uint112 r1,) = IPancakePair(pair).getReserves();
        if (r0 != 0 || r1 != 0) revert PoolNotEmpty();

        token.safeTransfer(pair, lpTokens);
        usdt.safeTransfer(pair, lpUsdt);
        IPancakePair(pair).mint(address(this));

        lpPair = pair;
        lpUnlockTime = block.timestamp + LP_LOCK;

        usdt.safeTransfer(devWallet, usdt.balanceOf(address(this))); // 40% (plus any swept dust)
        uint256 leftover = (SALE_TOKENS - tokensSold) + (LP_TOKENS_MAX - lpTokens);
        if (leftover > 0) token.safeTransfer(treasury, leftover);

        emit Finalized(raised, tokensSold, pair, lpUsdt, lpTokens, lpUnlockTime);
    }

    function claim() external nonReentrant returns (uint256 amount) {
        if (!finalized) revert NotFinalizable();
        amount = _vested(bought[msg.sender]) - claimed[msg.sender];
        if (amount == 0) revert NothingToClaim();
        claimed[msg.sender] += amount;
        token.safeTransfer(msg.sender, amount);
        emit Claimed(msg.sender, amount);
    }

    function claimable(address user) external view returns (uint256) {
        if (!finalized) return 0;
        return _vested(bought[user]) - claimed[user];
    }

    function refundable() public view returns (bool) {
        if (finalized) return false;
        if (block.timestamp < endTime) return false;
        return raised < softCap || block.timestamp >= endTime + FINALIZE_GRACE;
    }

    function refund() external nonReentrant {
        if (!refundable()) revert NotRefundable();
        uint256 amount = contributed[msg.sender];
        if (amount == 0) revert NothingToClaim();
        refundsStarted = true;
        contributed[msg.sender] = 0;
        bought[msg.sender] = 0;
        usdt.safeTransfer(msg.sender, amount);
        emit Refunded(msg.sender, amount);
    }

    /// @notice If the sale failed, send the deposited Tavorix back to the treasury.
    function returnTokensToTreasury() external nonReentrant {
        if (!refundable() || tokensReturned) revert NotRefundable();
        tokensReturned = true;
        token.safeTransfer(treasury, token.balanceOf(address(this)));
    }

    /// @notice After the 24-month lock, LP tokens go to the treasury (multisig + timelock).
    function releaseLP() external nonReentrant {
        if (!finalized) revert NotFinalizable();
        if (block.timestamp < lpUnlockTime) revert StillLocked();
        uint256 bal = IERC20(lpPair).balanceOf(address(this));
        IERC20(lpPair).safeTransfer(treasury, bal);
        emit LPReleased(treasury, bal);
    }

    function _vested(uint256 total) private view returns (uint256) {
        uint256 tge = (total * TGE_BPS) / 10_000;
        uint256 elapsed = block.timestamp - finalizedAt;
        if (elapsed >= VEST_DURATION) return total;
        return tge + ((total - tge) * elapsed) / VEST_DURATION;
    }
}
