#!/usr/bin/env python3
"""
Pytest-based tests for rm_referee_protocol_rs.

Requires the extension to be importable (e.g., via `maturin develop`).
"""

from __future__ import annotations

import pytest

HEX_STR = "A5 0B 00 00 5B 01 00 34 7B 00 C8 01 00 00 00 00 00 00 C7 08"


def hex_dump(b: bytes) -> str:
    return b.hex(" ").upper()


@pytest.fixture(scope="module")
def mod():
    import rm_referee_protocol_py as m

    return m


def test_parse_and_introspect_from_hex(mod):
    buf = bytes.fromhex(HEX_STR)
    frame = mod.RefereeFramePy(buf)

    # repr works and header is accessible
    assert isinstance(str(frame), str)
    h = frame.header
    assert isinstance(h.data_length, int)
    assert isinstance(h.seq, int)
    assert isinstance(h.crc8, int)

    # cmd_id equals the little-endian prefix of cmd_data_bytes
    cmd_bytes = frame.cmd_data_bytes()
    assert isinstance(cmd_bytes, (bytes, bytearray))
    if len(cmd_bytes) >= 2:
        expected_id = int.from_bytes(cmd_bytes[:2], "little")
        assert frame.cmd_id() == expected_id

    # Round-trip shouldn't corrupt cmd_id
    out = frame.to_bytes()
    reparsed = mod.RefereeFramePy(out)
    assert reparsed.cmd_id() == frame.cmd_id()


def test_seq_update_round_trip(mod):
    frame = mod.RefereeFramePy(bytes.fromhex(HEX_STR))
    new_seq = (frame.seq + 1) % 256
    frame.seq = new_seq
    out = frame.to_bytes()
    reparsed = mod.RefereeFramePy(out)
    assert reparsed.header.seq == new_seq


def test_modify_gamestatus_if_present(mod):
    frame = mod.RefereeFramePy(bytes.fromhex(HEX_STR))
    d = frame.cmd_data_py()
    if "GameStatus" not in d:
        pytest.skip("sample hex is not GameStatus; skipping mutation test")

    before = int(d["GameStatus"].get("stage_remain_time", 0))
    d["GameStatus"]["stage_remain_time"] = (before + 10) % 60000
    frame.set_cmd_data_py(d)
    out = frame.to_bytes()
    reparsed = mod.RefereeFramePy(out)
    after = reparsed.cmd_data_py()["GameStatus"]["stage_remain_time"]
    assert after == (before + 10) % 60000


def test_build_robotpos_and_buff_variants(mod):
    frame = mod.RefereeFramePy(bytes.fromhex(HEX_STR))

    # RobotPos (0x0203)
    rp = {"RobotPos": {"x": 1.25, "y": 2.5, "angle": 3.75}}
    frame.set_cmd_data_py(rp)
    out = frame.to_bytes()
    parsed = mod.RefereeFramePy(out)
    assert parsed.cmd_id() == 0x0203

    # Buff (0x0204)
    buff = {
        "Buff": {
            "recovery_buff": 1,
            "cooling_buff": 2,
            "defense_buff": 3,
            "vulnerability_buff": 4,
            "attack_buff": 123,
            "energy_ge_50": True,
            "energy_ge_30": False,
            "energy_ge_15": False,
            "energy_ge_5": False,
            "energy_ge_1": True,
            "energy_reserved": 0,
        }
    }
    frame.set_cmd_data_py(buff)
    out2 = frame.to_bytes()
    parsed2 = mod.RefereeFramePy(out2)
    assert parsed2.cmd_id() == 0x0204
    bdict = parsed2.cmd_data_py()["Buff"]
    assert bdict["attack_buff"] == 123
    assert bdict["energy_ge_50"] is True
    assert bdict["energy_ge_1"] is True


def test_send_only_construct_robotpos(mod):
    seq = 7
    tx = mod.RefereeFramePy.from_cmd_py(
        seq, {"RobotPos": {"x": 10.0, "y": 20.0, "angle": 30.0}}
    )
    out = tx.to_bytes()
    parsed = mod.RefereeFramePy(out)
    assert parsed.cmd_id() == 0x0203
    assert parsed.header.seq == seq
