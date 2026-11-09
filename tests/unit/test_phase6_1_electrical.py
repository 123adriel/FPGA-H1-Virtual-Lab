"""
Pytest Unit Test Suite for Phase 6.1 Discrete Hardware Electrical Verification
"""

import pytest
from scripts.verify_discrete_electrical import DiscreteCLBPrototype


@pytest.fixture
def clb():
    return DiscreteCLBPrototype()


def test_discrete_combinational_logic(clb):
    # Masks: AND=0x8888, OR=0xEEEE, XOR=0x6996, NOT=0x5555
    clb.configure(
        masks=[0x8888, 0xEEEE, 0x6996, 0x5555],
        bypass_bits=[1, 1, 1, 1],
        carry_bits=[0, 0, 0, 0]
    )
    for a in [0, 1]:
        for b in [0, 1]:
            in_vec = [a, b, 0, 0, a, b, 0, 0, a, b, 0, 0, a, b, 0, 0]
            res = clb.step(in_vec)
            assert res["OUT0"] == (a & b)
            assert res["OUT1"] == (a | b)
            assert res["OUT2"] == (a ^ b)
            assert res["OUT3"] == (1 - a)


def test_discrete_mux_logic(clb):
    clb.configure(
        masks=[0x00CA, 0, 0, 0],
        bypass_bits=[1, 1, 1, 1],
        carry_bits=[0, 0, 0, 0]
    )
    res0 = clb.step([1, 0, 0, 0] + [0]*12)
    assert res0["OUT0"] == 1
    res1 = clb.step([0, 1, 1, 0] + [0]*12)
    assert res1["OUT0"] == 1


def test_discrete_synchronous_counter(clb):
    clb.configure(
        masks=[0x5555, 0x6666, 0x7878, 0x7F80],
        bypass_bits=[0, 0, 0, 0],  # DFF Registered Mode
        carry_bits=[0, 0, 0, 0]
    )
    clb.step([0]*16, clk=0, async_clr_n=0)
    assert clb.dff0.q == 0 and clb.dff1.q == 0 and clb.dff2.q == 0 and clb.dff3.q == 0

    for expected_count in range(16):
        curr_val = clb.dff0.q | (clb.dff1.q << 1) | (clb.dff2.q << 2) | (clb.dff3.q << 3)
        assert curr_val == expected_count

        q0, q1, q2, q3 = clb.dff0.q, clb.dff1.q, clb.dff2.q, clb.dff3.q
        in_cnt = [q0, 0, 0, 0,   q0, q1, 0, 0,   q0, q1, q2, 0,   q0, q1, q2, q3]
        clb.step(in_cnt, clk=0, async_clr_n=1)
        clb.step(in_cnt, clk=1, async_clr_n=1)


def test_discrete_fast_carry_adder(clb):
    clb.configure(
        masks=[0x6666, 0x6666, 0x6666, 0x6666],
        bypass_bits=[1, 1, 1, 1],
        carry_bits=[1, 1, 1, 1]
    )
    for a_val in [0, 5, 7, 10, 15]:
        for b_val in [0, 3, 8, 9, 15]:
            a_bits = [(a_val >> i) & 1 for i in range(4)]
            b_bits = [(b_val >> i) & 1 for i in range(4)]
            in_vec = [
                a_bits[0], b_bits[0], 0, 0,
                a_bits[1], b_bits[1], 0, 0,
                a_bits[2], b_bits[2], 0, 0,
                a_bits[3], b_bits[3], 0, 0
            ]
            out = clb.step(in_vec, cin=0)
            sum_res = out["OUT0"] | (out["OUT1"] << 1) | (out["OUT2"] << 2) | (out["OUT3"] << 3)
            expected_sum = (a_val + b_val) & 0xF
            expected_cout = (a_val + b_val) >> 4
            assert sum_res == expected_sum
            assert out["COUT"] == expected_cout
