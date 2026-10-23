// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {SafeCast} from "@openzeppelin/contracts/utils/math/SafeCast.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title VestingVault
/// @notice Trust-minimised vesting: TGE unlock, optional cliff, then linear release.
///         Schedules are fully funded when created, cannot be revoked, and the
///         admin can permanently seal the vault so no new schedules can ever be added.
/// @dev Schedule math: before start -> 0. From start -> TGE portion.
///      After start+cliff -> TGE + (rest * elapsedSinceCliff / duration), capped at total.
contract VestingVault is ReentrancyGuard {
    using SafeERC20 for IERC20;
    using SafeCast for uint256;

    struct Schedule {
        uint128 total;
        uint128 claimed;
        uint64 start;
        uint64 cliff;     // seconds after start before linear vesting begins
        uint64 duration;  // seconds of linear vesting after the cliff
        uint16 tgeBps;    // share unlocked at start, in basis points
    }

    IERC20 public immutable token;
    address public immutable admin; // use a multisig
    bool public sealed_;
    uint256 public totalOwed; // allocated and not yet claimed

    mapping(address => Schedule[]) private _schedules;

    event ScheduleCreated(address indexed beneficiary, uint256 indexed id, uint256 total, uint64 start, uint64 cliff, uint64 duration, uint16 tgeBps);
    event Claimed(address indexed beneficiary, uint256 indexed id, uint256 amount);
    event Sealed();

    error NotAdmin();
    error IsSealed();
    error ZeroAddress();
    error ZeroAmount();
    error BadParams();
    error NothingToClaim();

    constructor(IERC20 token_, address admin_) {
        if (address(token_) == address(0) || admin_ == address(0)) revert ZeroAddress();
        token = token_;
        admin = admin_;
    }

    modifier onlyAdmin() {
        if (msg.sender != admin) revert NotAdmin();
        _;
    }

    /// @notice Create a schedule; tokens are pulled from the admin so the vault is always fully funded.
    function createSchedule(
        address beneficiary,
        uint256 total,
        uint64 start,
        uint64 cliff,
        uint64 duration,
        uint16 tgeBps
    ) external onlyAdmin nonReentrant {
        if (sealed_) revert IsSealed();
        if (beneficiary == address(0)) revert ZeroAddress();
        if (total == 0) revert ZeroAmount();
        if (tgeBps > 10_000 || (duration == 0 && tgeBps != 10_000)) revert BadParams();

        _schedules[beneficiary].push(
            Schedule(total.toUint128(), 0, start, cliff, duration, tgeBps)
        );
        totalOwed += total;
        token.safeTransferFrom(msg.sender, address(this), total);

        emit ScheduleCreated(beneficiary, _schedules[beneficiary].length - 1, total, start, cliff, duration, tgeBps);
    }

    /// @notice Permanently disable creation of new schedules.
    function seal() external onlyAdmin {
        sealed_ = true;
        emit Sealed();
    }

    function claim(uint256 id) external nonReentrant returns (uint256 amount) {
        Schedule storage s = _schedules[msg.sender][id];
        amount = _vested(s) - s.claimed;
        if (amount == 0) revert NothingToClaim();
        s.claimed += amount.toUint128();
        totalOwed -= amount;
        token.safeTransfer(msg.sender, amount);
        emit Claimed(msg.sender, id, amount);
    }

    function claimable(address beneficiary, uint256 id) external view returns (uint256) {
        Schedule storage s = _schedules[beneficiary][id];
        return _vested(s) - s.claimed;
    }

    function scheduleOf(address beneficiary, uint256 id) external view returns (Schedule memory) {
        return _schedules[beneficiary][id];
    }

    function scheduleCount(address beneficiary) external view returns (uint256) {
        return _schedules[beneficiary].length;
    }

    function _vested(Schedule storage s) private view returns (uint256) {
        if (block.timestamp < s.start) return 0;
        uint256 total = s.total;
        uint256 tge = (total * s.tgeBps) / 10_000;
        uint256 linearStart = uint256(s.start) + s.cliff;
        if (block.timestamp < linearStart) return tge;
        if (s.duration == 0) return total;
        uint256 elapsed = block.timestamp - linearStart;
        if (elapsed >= s.duration) return total;
        return tge + ((total - tge) * elapsed) / s.duration;
    }
}
