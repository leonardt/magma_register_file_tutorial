import math
import magma as m

def APBBase(addr_width: int, data_width: int):
    """
    Constructs a dictionary mapping port names to magma types
    
    Used to construct the master and slave variants of the APB inteface
    
    Parametrized by width of the address and data bus
    """
    return {
        "PCLK"   : m.Out(m.Clock),
        "PRESETn": m.Out(m.Reset),
        "PADDR"  : m.Out(m.Bits[addr_width]),
        "PPROT"  : m.Out(m.Bit),
        "PENABLE": m.Out(m.Bit),
        "PWRITE" : m.Out(m.Bit),
        "PWDATA" : m.Out(m.Bits[data_width]),
        # One write strobe bit for each byte of the data bus
        "PSTRB"  : m.Out(m.Bits[math.ceil(data_width / 8)]),
        "PREADY" : m.In(m.Bit),
        "PRDATA" : m.In(m.Bits[data_width]),
        "PSLVERR": m.In(m.Bit),
    }

def APBMaster(addr_width: int, data_width: int, num_sel: int=1):
    """
    Constructs the master variant of the APB interface using APBBase
    
    Parametrized by the width of the address and data bus as well as the number
    of slaves (`num_sel`)
    """
    if not data_width <= 32:
        raise ValueError("AMBA 3 APB specifies that the data bus " \
                         "cannot be wider than 32 bits")
    
    # Construct dictionary with a PSELx port for each slave
    fields = {}
    for i in range(num_sel):
        fields[f"PSEL{i}"] = m.Out(m.Bit)
        
    fields.update
        
    # Concatenate the APBBase dictionary with the PSEL dictionary to 
    # generate the full interface
    fields.update(APBBase(addr_width, data_width))
    
    return m.Product.from_fields("APBMaster", fields)


from typing import List, Union

def APBSlave(addr_width: int, data_width: int, 
             slave_id_or_ids: Union[int, List[int]]):
    """
    Constructs the slave variant of the APB interface using APBBase
    
    Parametrized by the with of the address and data bus as well as
    the slave id or a list of slave ids (to support lifting the
    APBSlave interface for a module that contains multiple slave 
    instances)
    
    `slave_id_or_ids` is either an id (e.g. 2) or a list of ids ([0, 1, 2])
    """
    # If the `slave_id_or_ids` parameter is a single integer, we convert it to
    # a list of a single integer so the rest of the code can assume that it is
    # a list of integers, otherwise, we check that it is a list of integers
    if isinstance(slave_id_or_ids, int):
        slave_id_or_ids = [slave_id_or_ids]
    elif not isinstance(slave_id_or_ids, list) and \
         all(isinstance(x, int) for x in slave_or_slave_ids):
        raise ValueError(f"Received incorrect parameter for "
                         f"`slave_or_slave_ids`: {slave_or_slave_ids}")
    
    # APBBase is defined in terms of the master, so we define PSEL as an output
    # since the entire type will be flipped
    fields = {f"PSEL{slave_id}": m.Out(m.Bit) for slave_id in slave_id_or_ids}
    fields.update(APBBase(addr_width, data_width))
    
    # Note the use of `flip()` to return the inverse of the type created by
    # APBBase
    return m.Product.from_fields("APBSlave", fields).flip()
