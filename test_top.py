from top import TopGenerator
import fault
from apb_model import APBBus, APBBusIO, Request, APB, APBCommand, \
    set_apb_inputs, make_request, step, write, read
import magma as m
import pytest


dma_fields = ["csr", "src_addr", "dst_addr", "txfr_len"]


@pytest.mark.parametrize("mode, num_slaves", [("pack", 1), ("distribute", 2)])
def test_top_simple_write(mode, num_slaves):
    Top = TopGenerator(mode=mode)

    tester = fault.Tester(Top, clock=Top.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = len(Top.apb.PADDR)
    data_width = len(Top.apb.PWDATA)
    bus = APBBus(addr_width, data_width, num_slaves)
    for i in range(2):
        for addr, field in enumerate(dma_fields):
            if mode == "pack":
                addr += i * len(dma_fields)
                slave_id = 0
            else:
                slave_id = i
            data = fault.random.random_bv(data_width)
            io, request = make_request(addr, data, addr_width, data_width,
                                       num_slaves, slave_id)

            write(bus, io, request, tester, addr, data)
            if mode == "pack":
                getattr(tester.circuit.reg_file, f"{field}{i}_q").expect(data)
            else:
                getattr(getattr(tester.circuit, f"reg_file{i}"),
                        f"{field}_q").expect(data)
            getattr(getattr(tester.circuit, f"dma{i}"),
                    f"{field}").expect(data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])


@pytest.mark.parametrize("mode, num_slaves", [("pack", 1), ("distribute", 2)])
def test_top_simple_write_read(mode, num_slaves):
    Top = TopGenerator(mode=mode)

    tester = fault.Tester(Top, clock=Top.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = len(Top.apb.PADDR)
    data_width = len(Top.apb.PWDATA)
    bus = APBBus(addr_width, data_width, num_slaves)
    for i in range(2):
        for addr, field in enumerate(dma_fields):
            if mode == "pack":
                addr += i * len(dma_fields)
                slave_id = 0
            else:
                slave_id = i
            data = fault.random.random_bv(data_width)
            io, request = make_request(addr, data, addr_width, data_width,
                                       num_slaves, slave_id)

            write(bus, io, request, tester, addr, data)
            getattr(getattr(tester.circuit, f"dma{i}"),
                    f"{field}").expect(data)
            read(bus, io, request, tester, addr, data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])


@pytest.mark.parametrize("mode, num_slaves", [("pack", 1), ("distribute", 2)])
def test_top_write_then_reads(mode, num_slaves):
    Top = TopGenerator(mode=mode)

    tester = fault.Tester(Top, clock=Top.apb.PCLK)
    tester.circuit.apb.PRESETn = 1

    addr_width = len(Top.apb.PADDR)
    data_width = len(Top.apb.PWDATA)
    bus = APBBus(addr_width, data_width, num_slaves)
    expected_values = []
    for i in range(2):
        for addr, field in enumerate(dma_fields):
            if mode == "pack":
                addr += i * len(dma_fields)
                slave_id = 0
            else:
                slave_id = i
            data = fault.random.random_bv(data_width)
            expected_values.append(data)
            io, request = make_request(addr, data, addr_width, data_width,
                                       num_slaves, slave_id)
            write(bus, io, request, tester, addr, data)

    for i in range(2):
        for addr, field in enumerate(dma_fields):
            data = expected_values[addr + i * len(dma_fields)]
            if mode == "pack":
                addr += i * len(dma_fields)
                slave_id = 0
            else:
                slave_id = i
            io, request = make_request(addr, data, addr_width, data_width,
                                       num_slaves, slave_id)
            getattr(getattr(tester.circuit, f"dma{i}"),
                    f"{field}").expect(data)
            read(bus, io, request, tester, addr, data)

    tester.compile_and_run(target="verilator", magma_output="coreir-verilog",
                           magma_opts={"verilator_debug": True},
                           flags=["--trace"])
