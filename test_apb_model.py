"""
TODO
====

Test PSTRB logic
"""
from apb_model import APBBus, APBBusIO, Request, APB, APBCommand, \
    default_APB_instance
from hwtypes import BitVector, Bit
from dataclasses import fields
from waveform import WaveForm


def test_apb_model_write_no_wait():
    addr_width = 16
    data_width = 32
    bus = APBBus(addr_width, data_width)
    addr = 13
    data = 45
    request = Request(addr_width, data_width, 1)(
        APBCommand.IDLE, BitVector[addr_width](addr),
        BitVector[data_width](data), BitVector[1](0))

    # Specialized instance of APB for addr/data width
    _APB = APB(addr_width, data_width)

    io = APBBusIO(addr_width, data_width)(default_APB_instance(_APB), request)

    apb_fields = (field for field in _APB.field_dict)
    waveform = WaveForm(apb_fields, clock_name="PCLK")

    # check idle stae
    for i in range(1):
        bus(io)
        waveform.step(bus.io.apb)

    # Send request
    request.command = APBCommand.WRITE
    bus(io)
    assert io.apb.PSEL0 == 1

    waveform.step(bus.io.apb)

    request.command = APBCommand.IDLE

    # No wait state
    io.apb.PREADY = Bit(1)
    bus(io)
    waveform.step(bus.io.apb)

    assert io.apb.PENABLE == 1
    assert io.apb.PSEL0 == 1

    bus(io)
    # Slave pulls PREADY down at the same time
    io.apb.PREADY = Bit(0)
    waveform.step(bus.io.apb)

    assert io.apb.PENABLE == 0
    assert io.apb.PSEL0 == 0

    io.apb.PWDATA = BitVector[data_width](0)

    bus(io)
    waveform.step(bus.io.apb)
    assert waveform.to_wavejson() == """\
{
    "signal": [
        {
            "name": "PCLK",
            "wave": "p...."
        },
        {
            "name": "PADDR",
            "wave": "==...",
            "data": [
                "0x0",
                "0xd"
            ]
        },
        {
            "name": "PWRITE",
            "wave": "01..."
        },
        {
            "name": "PSEL0",
            "wave": "01.0."
        },
        {
            "name": "PENABLE",
            "wave": "0.10."
        },
        {
            "name": "PWDATA",
            "wave": "==..=",
            "data": [
                "0x0",
                "0x2d",
                "0x0"
            ]
        },
        {
            "name": "PRDATA",
            "wave": "=....",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PREADY",
            "wave": "0.10."
        },
        {
            "name": "PSTRB",
            "wave": "=....",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PPROT",
            "wave": "0...."
        },
        {
            "name": "SLVERR",
            "wave": "0...."
        }
    ]
}""", waveform.render()  # Render if fails


def test_apb_model_write_with_wait():
    addr_width = 16
    data_width = 32
    bus = APBBus(addr_width, data_width)
    addr = 13
    data = 45
    request = Request(addr_width, data_width, 1)(
        APBCommand.IDLE, BitVector[addr_width](addr), BitVector[data_width](data), BitVector[1](0))

    # Specialized instance of APB for addr/data width
    _APB = APB(addr_width, data_width)

    io = APBBusIO(addr_width, data_width)(
        default_APB_instance(_APB), request)

    apb_fields = (field for field in _APB.field_dict)
    waveform = WaveForm(apb_fields, clock_name="PCLK")

    # check idle stae
    for i in range(1):
        bus(io)
        waveform.step(bus.io.apb)

    # Send request
    request.command = APBCommand.WRITE
    bus(io)
    waveform.step(bus.io.apb)
    assert io.apb.PSEL0 == 1
    assert io.apb.PWRITE == 1

    request.command = APBCommand.IDLE

    # Wait by holding PREADY down
    io.apb.PREADY = Bit(0)
    bus(io)
    waveform.step(bus.io.apb)
    assert io.apb.PENABLE == 1
    assert io.apb.PSEL0 == 1
    assert io.apb.PWRITE == 1

    for i in range(2):
        bus(io)
        waveform.step(bus.io.apb)
        assert io.apb.PENABLE == 1
        assert io.apb.PSEL0 == 1
        assert io.apb.PWRITE == 1

    bus(io)
    # PREADY high when done
    io.apb.PREADY = Bit(1)
    waveform.step(bus.io.apb)
    bus(io)
    io.apb.PREADY = Bit(0)
    io.apb.PWDATA = BitVector[data_width](0)
    waveform.step(bus.io.apb)
    assert io.apb.PENABLE == 0
    assert io.apb.PSEL0 == 0
    assert waveform.to_wavejson() == """\
{
    "signal": [
        {
            "name": "PCLK",
            "wave": "p......"
        },
        {
            "name": "PADDR",
            "wave": "==.....",
            "data": [
                "0x0",
                "0xd"
            ]
        },
        {
            "name": "PWRITE",
            "wave": "01....."
        },
        {
            "name": "PSEL0",
            "wave": "01....0"
        },
        {
            "name": "PENABLE",
            "wave": "0.1...0"
        },
        {
            "name": "PWDATA",
            "wave": "==....=",
            "data": [
                "0x0",
                "0x2d",
                "0x0"
            ]
        },
        {
            "name": "PRDATA",
            "wave": "=......",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PREADY",
            "wave": "0....10"
        },
        {
            "name": "PSTRB",
            "wave": "=......",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PPROT",
            "wave": "0......"
        },
        {
            "name": "SLVERR",
            "wave": "0......"
        }
    ]
}""", waveform.render()  # Render if fails


def test_apb_model_read_no_wait():
    addr_width = 16
    data_width = 32
    bus = APBBus(addr_width, data_width)
    addr = 13
    data = 0
    request = Request(addr_width, data_width, 1)(
        APBCommand.IDLE, BitVector[addr_width](addr), BitVector[data_width](data), BitVector[1](0))

    # Specialized instance of APB for addr/data width
    _APB = APB(addr_width, data_width)

    io = APBBusIO(addr_width, data_width)(default_APB_instance(_APB), request)

    apb_fields = (field for field in _APB.field_dict)
    waveform = WaveForm(apb_fields, clock_name="PCLK")

    # check idle stae
    for i in range(1):
        bus(io)
        waveform.step(bus.io.apb)

    # Send request
    request.command = APBCommand.READ
    bus(io)
    waveform.step(bus.io.apb)

    request.command = APBCommand.IDLE

    bus(io)
    waveform.step(bus.io.apb)
    assert io.apb.PENABLE == 1

    # No wait state
    bus(io)
    io.apb.PREADY = Bit(1)
    io.apb.PRDATA = BitVector[data_width](13)
    waveform.step(bus.io.apb)

    bus(io)
    io.apb.PREADY = Bit(0)
    io.apb.PRDATA = BitVector[data_width](0)
    waveform.step(bus.io.apb)

    assert io.apb.PENABLE == 0
    assert io.apb.PSEL0 == 0
    assert waveform.to_wavejson() == """\
{
    "signal": [
        {
            "name": "PCLK",
            "wave": "p...."
        },
        {
            "name": "PADDR",
            "wave": "==...",
            "data": [
                "0x0",
                "0xd"
            ]
        },
        {
            "name": "PWRITE",
            "wave": "0...."
        },
        {
            "name": "PSEL0",
            "wave": "01..0"
        },
        {
            "name": "PENABLE",
            "wave": "0.1.0"
        },
        {
            "name": "PWDATA",
            "wave": "=....",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PRDATA",
            "wave": "=..==",
            "data": [
                "0x0",
                "0xd",
                "0x0"
            ]
        },
        {
            "name": "PREADY",
            "wave": "0..10"
        },
        {
            "name": "PSTRB",
            "wave": "=....",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PPROT",
            "wave": "0...."
        },
        {
            "name": "SLVERR",
            "wave": "0...."
        }
    ]
}""", waveform.render()  # Render if fails


def test_apb_model_read_with_wait():
    addr_width = 16
    data_width = 32
    bus = APBBus(addr_width, data_width)
    addr = 13
    data = 0
    request = Request(addr_width, data_width, 1)(
        APBCommand.IDLE, BitVector[addr_width](addr), BitVector[data_width](data), BitVector[1](0))

    # Specialized instance of APB for addr/data width
    _APB = APB(addr_width, data_width)

    io = APBBusIO(addr_width, data_width)(default_APB_instance(_APB), request)

    apb_fields = (field for field in _APB.field_dict)
    waveform = WaveForm(apb_fields, clock_name="PCLK")

    # check idle stae
    for i in range(1):
        bus(io)
        waveform.step(bus.io.apb)

    # Send request
    request.command = APBCommand.READ
    bus(io)
    waveform.step(bus.io.apb)

    request.command = APBCommand.IDLE

    bus(io)
    waveform.step(bus.io.apb)
    assert io.apb.PENABLE == 1

    for i in range(2):
        bus(io)
        waveform.step(bus.io.apb)

    bus(io)
    io.apb.PREADY = Bit(1)
    io.apb.PRDATA = BitVector[data_width](13)
    waveform.step(bus.io.apb)

    bus(io)
    io.apb.PREADY = Bit(0)
    io.apb.PRDATA = BitVector[data_width](0)
    waveform.step(bus.io.apb)

    assert io.apb.PENABLE == 0
    assert io.apb.PSEL0 == 0
    assert waveform.to_wavejson() == """\
{
    "signal": [
        {
            "name": "PCLK",
            "wave": "p......"
        },
        {
            "name": "PADDR",
            "wave": "==.....",
            "data": [
                "0x0",
                "0xd"
            ]
        },
        {
            "name": "PWRITE",
            "wave": "0......"
        },
        {
            "name": "PSEL0",
            "wave": "01....0"
        },
        {
            "name": "PENABLE",
            "wave": "0.1...0"
        },
        {
            "name": "PWDATA",
            "wave": "=......",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PRDATA",
            "wave": "=....==",
            "data": [
                "0x0",
                "0xd",
                "0x0"
            ]
        },
        {
            "name": "PREADY",
            "wave": "0....10"
        },
        {
            "name": "PSTRB",
            "wave": "=......",
            "data": [
                "0x0"
            ]
        },
        {
            "name": "PPROT",
            "wave": "0......"
        },
        {
            "name": "SLVERR",
            "wave": "0......"
        }
    ]
}""", waveform.render()  # Render if fails
