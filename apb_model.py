import math
from hwtypes import Enum, Product, Bit, BitVector
import apb
from functools import lru_cache, wraps
import inspect


def canonicalize_args(f):
    """Wrapper for functools.lru_cache() to canonicalize default
    and keyword arguments so cache hits are maximized."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        sig = inspect.getfullargspec(f.__wrapped__)

        # build newargs by filling in defaults, args, kwargs
        newargs = [None] * len(sig.args)
        if sig.defaults is not None:
            newargs[-len(sig.defaults):] = sig.defaults
        newargs[:len(args)] = args
        for name, value in kwargs.items():
            newargs[sig.args.index(name)] = value

        return f(*newargs)

    return wrapper


class APBCommand(Enum):
    READ = 0
    WRITE = 1
    IDLE = 2


@canonicalize_args
@lru_cache(maxsize=None)
def APB(addr_width, data_width, num_slaves=1):
    strobe_width = math.ceil(data_width / 8)

    fields = {
        "PADDR": BitVector[addr_width],
        "PWRITE": Bit,
    }

    for i in range(num_slaves):
        fields[f"PSEL{i}"] = Bit

    fields.update({
        "PENABLE": Bit,
        "PWDATA": BitVector[data_width],
        "PRDATA": BitVector[data_width],
        "PREADY": Bit,
        "PSTRB": BitVector[strobe_width],
        "PPROT": Bit,
        "SLVERR": Bit,
    })

    result = type("_APB", (Product, ), fields)
    return result


def default_APB_instance(_APB):
    """
    Convenience function to instantiate an _APB object with default values of 0
    """
    fields = {}
    for key, value in _APB.field_dict.items():
        fields[key] = value(0)
    return _APB(**fields)


@canonicalize_args
@lru_cache(maxsize=None)
def Request(addr_width, data_width, num_slaves):
    class _Request(Product):
        command = APBCommand
        address = BitVector[addr_width]
        data = BitVector[data_width]
        slave_id = BitVector[max(math.ceil(math.log2(num_slaves)), 1)]
    return _Request


@canonicalize_args
@lru_cache(maxsize=None)
def APBBusIO(addr_width, data_width, num_slaves=1):
    class IO(Product):
        apb = APB(addr_width, data_width, num_slaves)
        request = Request(addr_width, data_width, num_slaves)
    return IO


@canonicalize_args
@lru_cache(maxsize=None)
def APBBus(addr_width, data_width, num_slaves=1):

    class APBBus:
        def __init__(self):
            self.IO = APBBusIO(addr_width, data_width, num_slaves)
            # TODO: Move main logic to a base class
            self.main = self._main()
            next(self.main)

        def __call__(self, io):
            self.io = io
            self.main.send(None)

        def _main(self):
            yield
            while True:
                if self.io.request.command == APBCommand.READ:
                    yield from self.read(self.io.request.address,
                                         self.io.request.data)
                elif self.io.request.command == APBCommand.WRITE:
                    yield from self.write(self.io.request.address,
                                          self.io.request.data)
                else:
                    yield

        def set_psel(self, value):
            setattr(self.io.apb, f"PSEL{self.io.request.slave_id}", value)

        def write(self, address, data):
            self.io.apb.PADDR = address
            self.io.apb.PWDATA = data
            self.set_psel(Bit(1))
            self.io.apb.PWRITE = Bit(1)
            yield
            self.io.apb.PENABLE = Bit(1)
            yield
            while not self.io.apb.PREADY:
                # TODO: Insert timeout logic
                yield
            self.io.apb.PENABLE = Bit(0)
            self.set_psel(Bit(0))

        def read(self, address, data):
            self.io.apb.PADDR = address
            self.set_psel(Bit(1))
            self.io.apb.PWRITE = Bit(0)
            yield
            self.io.apb.PENABLE = Bit(1)
            yield
            while not self.io.apb.PREADY:
                # TODO: Insert timeout logic
                yield
            self.io.apb.PENABLE = Bit(0)
            self.set_psel(Bit(0))

            # TODO: Handle PSLVERR and checking the expected data
    return APBBus()


def set_apb_inputs(tester, bus):
    for key in tester._circuit.apb.keys():
        # Skip clock signals
        if key in ["PCLK", "PRESETn"]:
            continue
        if tester._circuit.apb[key].is_output():
            setattr(tester.circuit.apb, key,
                    getattr(bus.io.apb, key))


def make_request(addr, data, addr_width, data_width, num_slaves=1, slave_id=0):
    request = Request(addr_width, data_width, num_slaves)(
        APBCommand.IDLE, BitVector[addr_width](addr),
        BitVector[data_width](data),
        BitVector[max(math.ceil(math.log2(num_slaves)), 1)](slave_id))

    # Specialized instance of APB for addr/data width
    _APB = APB(addr_width, data_width, num_slaves)

    io = APBBusIO(addr_width, data_width,
                  num_slaves)(default_APB_instance(_APB), request)
    return io, request


def step(bus, io, tester):
    bus(io)
    set_apb_inputs(tester, bus)
    tester.step(2)


def write(bus, io, request, tester, addr, data):
    # Test idle state
    step(bus, io, tester)

    # Send request
    request.command = APBCommand.WRITE
    step(bus, io, tester)

    request.command = APBCommand.IDLE

    # No wait state
    io.apb.PREADY = Bit(1)
    step(bus, io, tester)

    tester.circuit.apb.PREADY.expect(1)

    step(bus, io, tester)

    tester.circuit.apb.PREADY.expect(0)
    tester.step(2)


def read(bus, io, request, tester, addr, data):
    # Send request
    request.command = APBCommand.READ
    step(bus, io, tester)

    request.command = APBCommand.IDLE

    # No wait state
    io.apb.PREADY = Bit(1)
    step(bus, io, tester)

    tester.circuit.apb.PREADY.expect(1)
    tester.circuit.apb.PRDATA.expect(data)
    step(bus, io, tester)

    tester.circuit.apb.PREADY.expect(0)
    tester.step(2)
