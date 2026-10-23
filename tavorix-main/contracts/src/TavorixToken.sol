// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import {ERC20Votes} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import {Nonces} from "@openzeppelin/contracts/utils/Nonces.sol";

/// @title TavorixToken
/// @notice Fixed-supply governance/utility token. No mint function, no owner, no pause.
/// @dev Entire supply is minted once in the constructor to pre-agreed recipients
///      (vesting vault, liquidity, treasury multisig, etc). Burns cannot take
///      total supply below SUPPLY_FLOOR.
contract TavorixToken is ERC20, ERC20Burnable, ERC20Permit, ERC20Votes {
    uint256 public constant TOTAL_SUPPLY = 510_000_000 ether;
    uint256 public constant SUPPLY_FLOOR = 400_000_000 ether;

    error LengthMismatch();
    error ZeroAddress();
    error BadTotal();
    error BurnBelowFloor();

    constructor(address[] memory recipients, uint256[] memory amounts)
        ERC20("Tavorix", "TVRX")
        ERC20Permit("Tavorix")
    {
        if (recipients.length != amounts.length) revert LengthMismatch();
        uint256 sum;
        for (uint256 i; i < recipients.length; ++i) {
            if (recipients[i] == address(0)) revert ZeroAddress();
            sum += amounts[i];
            _mint(recipients[i], amounts[i]);
        }
        if (sum != TOTAL_SUPPLY) revert BadTotal();
    }

    function _update(address from, address to, uint256 value)
        internal
        override(ERC20, ERC20Votes)
    {
        if (to == address(0) && totalSupply() - value < SUPPLY_FLOOR) revert BurnBelowFloor();
        super._update(from, to, value);
    }

    function nonces(address owner) public view override(ERC20Permit, Nonces) returns (uint256) {
        return super.nonces(owner);
    }
}
