#!/usr/bin/env python3
"""
rm_referee_protocol_rs quick tests (clean + readable).

Run after installing the extension (e.g. `maturin develop`):
  python scripts/test_frame_from_hex.py
"""

from __future__ import annotations

HEX_STR = "A5 0B 00 00 5B 01 00 34 7B 00 C8 01 00 00 00 00 00 00 C7 08"


def sep(title: str) -> None:
    print(f"\n=== {title} ===")


def hex_dump(b: bytes) -> str:
    return b.hex(" ").upper()


def show_header(frame) -> None:
    h = frame.header
    print("header.data_length:", h.data_length)
    print("header.seq:", h.seq)
    print("header.crc8:", h.crc8)


def tweak_seq(frame) -> None:
    print("seq(before):", frame.seq)
    frame.seq = (frame.seq + 1) % 256
    print("seq(after):", frame.seq)
    print("header.seq(after):", frame.header.seq)


def inspect_cmd(frame) -> None:
    print("cmd_id:", hex(frame.cmd_id()))
    print("cmd_data_bytes:", hex_dump(frame.cmd_data_bytes()))
    print("cmd_data_dict:", frame.cmd_data_py())


def maybe_modify_gamestatus(frame) -> None:
    d = frame.cmd_data_py()
    before = d.get("GameStatus", {}).get("stage_remain_time")
    print("stage_remain_time(before):", before)
    if "GameStatus" in d:
        d["GameStatus"]["stage_remain_time"] = (int(before or 0) + 10) % 60000
        frame.set_cmd_data_py(d)
        after = frame.cmd_data_py().get("GameStatus", {}).get("stage_remain_time")
        print("stage_remain_time(after):", after)
        print(
            "Serialized hex after stage_remain_time change:", hex_dump(frame.to_bytes())
        )


def build_and_check(mod, frame, variant: str, payload: dict, expected_id: int) -> bool:
    d = {variant: payload}
    frame.set_cmd_data_py(d)
    out_bytes = frame.to_bytes()
    parsed = mod.RefereeFramePy(out_bytes)
    got_id = parsed.cmd_id()
    cmd_bytes2 = parsed.cmd_data_bytes()
    id_le = int.from_bytes(cmd_bytes2[:2], "little") if len(cmd_bytes2) >= 2 else None
    ok = (got_id == expected_id) and (id_le == expected_id)
    print(f"[cmd {variant}] id={got_id:#06x}, expected={expected_id:#06x}, ok={ok}")
    print("serialized:", hex_dump(out_bytes))
    return ok


def send_only_construct_and_show(mod) -> None:
    new_cmd = {"RobotPos": {"x": 10.0, "y": 20.0, "angle": 30.0}}
    tx = mod.RefereeFramePy.from_cmd_py(7, new_cmd)
    tx_bytes = tx.to_bytes()
    print("[TX] RobotPos from scratch, seq=7 ->", hex_dump(tx_bytes))
    print("[TX] cmd_id:", hex(mod.RefereeFramePy(tx_bytes).cmd_id()))


def main() -> int:
    import rm_referee_protocol_py as mod

    try:
        sep("Parse + Introspect")
        frame = mod.RefereeFramePy(bytes.fromhex(HEX_STR))
        print("repr:", frame)
        show_header(frame)

        sep("Tweak seq and round-trip")
        tweak_seq(frame)
        print("Serialized hex after seq+1:", hex_dump(frame.to_bytes()))

        sep("Command details")
        inspect_cmd(frame)

        sep("Modify GameStatus example")
        maybe_modify_gamestatus(frame)

        sep("Build other variants and verify ids")
        all_ok = True
        all_ok &= build_and_check(
            mod, frame, "RobotPos", {"x": 1.25, "y": 2.5, "angle": 3.75}, 0x0203
        )
        all_ok &= build_and_check(
            mod,
            frame,
            "Buff",
            {
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
            },
            0x0204,
        )
        print("[RESULT] variant construction checks:", "OK" if all_ok else "FAIL")

        sep("Send-only construction")
        send_only_construct_and_show(mod)

        return 0
    except Exception as e:
        print("[FAIL]", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
