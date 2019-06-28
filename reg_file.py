import magma as m
import mantle
from apb import APBMaster, APBSlave
from mantle.coreir import Term, CorebitTerm


class Register:
    def __init__(self, name, init=0, has_ce=False):
        self.name = name
        self.init = init
        self.has_ce = has_ce


def DefineRegFile(reg_list, data_width, base_addr=0, apb_slave_id=0):
    """
    reg_list : list of Register instances
    """
    if base_addr != 0:
        raise NotImplementedError()
    addr_width = m.bitutils.clog2(len(reg_list))

    Data = m.Bits[data_width]

    class RegFile(m.Circuit):
        IO = ["apb", APBSlave(addr_width, data_width, apb_slave_id)]
        for reg in reg_list:
            IO += [f"{reg.name}_d", m.In(Data)]
            if reg.has_ce:
                IO += [f"{reg.name}_en", m.In(m.Enable)]
            IO += [f"{reg.name}_q", m.Out(Data)]

        @classmethod
        def definition(io):
            PSEL = getattr(io.apb, f"PSEL{apb_slave_id}")
            registers = [
                mantle.Register(data_width, init=reg.init, has_ce=True,
                                has_reset=True, name=reg.name)
                for reg in reg_list
            ]
            is_write = io.apb.PENABLE & io.apb.PWRITE & PSEL
            ready = None
            for i, reg in enumerate(registers):
                reg.I <= mantle.mux([getattr(io, reg.name + "_d"),
                                     io.apb.PWDATA], is_write)
                getattr(io, reg.name + "_q") <= reg.O
                reg.CLK <= io.apb.PCLK
                reg.RESET <= ~m.bit(io.apb.PRESETn)
                ce = is_write & (io.apb.PADDR == i)
                if reg_list[i].has_ce:
                    reg.CE <= ce | m.bit(getattr(io, reg.name + "_en"))
                else:
                    reg.CE <= ce
                if ready is not None:
                    ready |= ce
                else:
                    ready = ce
            is_read = io.apb.PENABLE & ~io.apb.PWRITE & PSEL
            io.apb.PREADY <= ready | is_read
            io.apb.PRDATA <= mantle.mux(
                [reg.O for reg in registers], io.apb.PADDR)
            io.apb.PSLVERR <= 0

            # Unused
            CorebitTerm().I <= io.apb.PPROT
            Term(len(io.apb.PSTRB)).I <= io.apb.PSTRB

    return RegFile

