from apb_model import APBBus, APBBusIO, Request, APB, APBCommand, \
    set_apb_inputs, make_request, step, write, read
from reg_file import RegisterFileGenerator, Register
import magma as m
import fault
from dataclasses import fields


def test_simple_write():
    data_width = 32
    regs = tuple(Register(f"reg_{i}", init=i, has_ce=True) for i in range(4))
    RegFile = RegisterFileGenerator(regs, data_width)
    tester = fault.Tester(RegFile, clock=RegFile.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = m.bitutils.clog2(len(regs))
    data_width = 32
    addr = 1
    data = 45
    bus = APBBus(addr_width, data_width)
    io, request = make_request(addr, data, addr_width, data_width)

    write(bus, io, request, tester, addr, data)
    getattr(tester.circuit, f"reg_{addr}_q").expect(data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])


def test_simple_write_read():
    data_width = 32
    regs = tuple(Register(f"reg_{i}", init=i, has_ce=True) for i in range(4))
    RegFile = RegisterFileGenerator(regs, data_width)
    tester = fault.Tester(RegFile, clock=RegFile.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = m.bitutils.clog2(len(regs))
    data_width = 32
    bus = APBBus(addr_width, data_width)
    addr = 1
    data = 45
    io, request = make_request(addr, data, addr_width, data_width)
    write(bus, io, request, tester, addr, data)

    read(bus, io, request, tester, addr, data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])


def test_write_then_reads():
    data_width = 32
    regs = tuple(Register(f"reg_{i}", init=i, has_ce=True) for i in range(4))
    RegFile = RegisterFileGenerator(regs, data_width)
    tester = fault.Tester(RegFile, clock=RegFile.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = m.bitutils.clog2(len(regs))
    data_width = 32
    bus = APBBus(addr_width, data_width)
    values = [0xDE, 0xAD, 0xBE, 0xEF]
    for addr, data in enumerate(values):
        io, request = make_request(addr, data, addr_width, data_width)
        write(bus, io, request, tester, addr, data)
        getattr(tester.circuit, f"reg_{addr}_q").expect(data)

    for addr, data in enumerate(values):
        io, request = make_request(addr, data, addr_width, data_width)
        read(bus, io, request, tester, addr, data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])
