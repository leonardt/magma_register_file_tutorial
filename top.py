import magma as m
from reg_file import DefineRegFile, Register
from apb import APBSlave, APBBase
import math
import mantle


class DMA(m.Circuit):
    """
    Stub DMA module
    """
    IO = ["csr", m.In(m.Bits[32]), "src_addr", m.In(m.Bits[32]),
          "dst_addr", m.In(m.Bits[32]), "txfr_len", m.In(m.Bits[32])]

    @classmethod
    def definition(io):
        mantle.coreir.DefineTerm(32)().I <= io.csr
        mantle.coreir.DefineTerm(32)().I <= io.src_addr
        mantle.coreir.DefineTerm(32)().I <= io.dst_addr
        mantle.coreir.DefineTerm(32)().I <= io.txfr_len


def DefineTop(mode="pack"):
    """
    Simple example that instances two stub DMA modules and is paramtrizable
    over distributed versus packed register file
    """

    if mode not in ["pack", "distribute"]:
        raise ValueError(f"Unexpected mode {mode}")

    fields = ["csr", "src_addr", "dst_addr", "txfr_len"]
    data_width = 32
    if mode == "pack":
        addr_width = math.ceil(math.log2(len(fields) * 2))
    else:
        addr_width = math.ceil(math.log2(len(fields)))

    class Top(m.Circuit):
        if mode == "pack":
            IO = ["apb", APBSlave(addr_width, data_width, 0)]
        else:
            IO = ["apb", APBSlave(addr_width, data_width, [0, 1])]

        @classmethod
        def definition(io):
            dmas = [DMA(name=f"dma{i}") for i in range(2)]
            if mode == "pack":
                regs = [Register(name + str(i)) for i in range(2) for name in
                        fields]
                reg_file = DefineRegFile(regs, data_width=32)(name="reg_file")
                for i in range(2):
                    for name in fields:
                        m.wire(getattr(reg_file, name + str(i) + "_q"),
                               getattr(dmas[i], name))
                m.wire(io.apb, reg_file.apb)
                for i in range(2):
                    for name in fields:
                        m.wire(getattr(reg_file, name + str(i) + "_q"),
                               getattr(reg_file, name + str(i) + "_d"))
            else:
                apb_outputs = {}
                for key, type_ in APBBase(addr_width, data_width).items():
                    if type_.isinput():
                        apb_outputs[key] = []
                for i in range(2):
                    regs = [Register(name) for name in fields]
                    reg_file = DefineRegFile(
                        regs, data_width=32, apb_slave_id=i
                    )(name=f"reg_file{i}")
                    for name in fields:
                        m.wire(getattr(reg_file, name + "_q"),
                               getattr(dmas[i], name))
                    for key, type_ in APBBase(addr_width, data_width).items():
                        if type_.isoutput():
                            m.wire(getattr(io.apb, key),
                                   getattr(reg_file.apb, key))
                        else:
                            apb_outputs[key].append(getattr(reg_file.apb, key))
                    m.wire(getattr(io.apb, f"PSEL{i}"),
                           getattr(reg_file.apb, f"PSEL{i}"))
                    for name in fields:
                        m.wire(getattr(reg_file, name + "_q"),
                               getattr(reg_file, name + "_d"))
                for key, values in apb_outputs.items():
                    m.wire(getattr(io.apb, key),
                           mantle.mux(values, io.apb.PSEL1))
    return Top
