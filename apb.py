import math
import magma as m

# Possibly useful reference w/ Verilog code: https://www.verilog.pro/apb.html


def APBBase(addr_width, data_width):
    return {
        "PCLK": m.Out(m.Clock),
        "PRESETn": m.Out(m.Reset),
        "PADDR": m.Out(m.Bits[addr_width]),
        "PPROT": m.Out(m.Bit),
        "PENABLE": m.Out(m.Bit),
        "PWRITE": m.Out(m.Bit),
        "PWDATA": m.Out(m.Bits[data_width]),
        # One write strobe bit for each byte of the data bus
        "PSTRB": m.Out(m.Bits[math.ceil(data_width / 8)]),
        "PREADY": m.In(m.Bit),
        "PRDATA": m.In(m.Bits[data_width]),
        "PSLVERR": m.In(m.Bit),
    }


def APBMaster(addr_width, data_width, num_sel=1):
    assert data_width <= 32
    PSELs = {}
    for i in range(num_sel):
        PSELs[f"PSEL{i}"] = m.Out(m.Bit)
    return m.Tuple(
        **APBBase(addr_width, data_width),
        **PSELs,
    )


def APBSlave(addr_width, data_width, slave_id_or_ids):
    """
    slave_id_or_ids is either an id (e.g. 2) or a list of ids ([0, 1, 2])
    """
    if isinstance(slave_id_or_ids, int):
        slave_id_or_ids = [slave_id_or_ids]
    # APBBase is defined in terms of the master, so we define PSEL as an output
    # since the entire type will be flipped
    PSEL = {f"PSEL{slave_id}": m.Out(m.Bit) for slave_id in slave_id_or_ids}
    return m.Tuple(**APBBase(addr_width, data_width), **PSEL).flip()
