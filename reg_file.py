import magma as m
import mantle
from apb import APBMaster, APBSlave
from typing import Tuple


class Register:
    def __init__(self, name, init=0, has_ce=False):
        self.name = name
        self.init = init
        self.has_ce = has_ce
        

def make_reg_file_interface(reg_list: Tuple[Register], data_width: int,
                            apb_slave_id: int):
    # magma provides various helper functions in m.bitutils, 
    # here we use clog2 to derive the number of bits required 
    # to store the address space described by number of Registers 
    # in `reg_list`
    addr_width = m.bitutils.clog2(len(reg_list))
    
    Data = m.Bits[data_width]
    
    io = m.IO(apb=APBSlave(addr_width, data_width, apb_slave_id))
    for reg in reg_list:
        io += m.IO(**{f"{reg.name}_d": m.In(Data)})
        if reg.has_ce:
            io += m.IO(**{f"{reg.name}_en": m.In(m.Enable)})
        io += m.IO(**{f"{reg.name}_q": m.Out(Data)})
    return io


class RegisterFileGenerator(m.Generator2):
    def __init__(self, regs, data_width, apb_slave_id=0):
        """
        regs : tuple of Register instances
        """
        self.name = "RegFile_" + "_".join(reg.name for reg in regs)
        self.io = io = make_reg_file_interface(regs, data_width, apb_slave_id)

        # Get the concrete PSEL signal based on the `apb_slave_id`
        # parameter
        PSEL = getattr(io.apb, f"PSEL{apb_slave_id}")

        # Create a list of Register instances (parametrized by the members
        # of `regs`)
        registers = [
            mantle.Register(data_width, init=reg.init, has_ce=True,
                            has_reset=True, name=reg.name)
            for reg in regs
        ]

        is_write = io.apb.PENABLE & io.apb.PWRITE & PSEL

        ready = None
        for i, reg in enumerate(registers):
            # Register input is from `<reg_name>_d` port by default
            # and PWDATA when handling an APB write
            reg.I @= mantle.mux([getattr(io, reg.name + "_d"),
                                 io.apb.PWDATA], is_write)

            # Wire up register output to `<reg_name>_q` interface port
            getattr(io, reg.name + "_q") <= reg.O

            # Wire the clock signals
            reg.CLK @= io.apb.PCLK
            reg.RESET @= ~m.bit(io.apb.PRESETn)

            # Clock enable is based on write signal and PADDR value
            # For now, a register's address is defined by its index in
            # `regs`
            ce = is_write & (io.apb.PADDR == i)
            if regs[i].has_ce:
                # If has a clock enable, `or` the enable signal with the IO
                # input
                reg.CE @= ce | m.bit(getattr(io, reg.name + "_en"))
            else:
                reg.CE @= ce

            # Set ready high if a register is being written to
            if ready is not None:
                ready |= ce
            else:
                ready = ce

        is_read = io.apb.PENABLE & ~io.apb.PWRITE & PSEL

        # PREADY is high if a write or read is being performed
        io.apb.PREADY @= ready | is_read

        # Select PRDATA based on PADDR
        io.apb.PRDATA @= mantle.mux(
            [reg.O for reg in registers], io.apb.PADDR)

        # Stub out the rest of the signals for now, CoreIR does not allow
        # unconnected signals, so we wire them up to the CoreIR `Term`
        # module which is a stub module that takes a single input and no
        # output (effectively "casting" the unwired port so the compiler
        # does not complain)
        io.apb.PSLVERR.undriven()
        io.apb.PPROT.unused()
        io.apb.PSTRB.unused()
