import pyrtl
from enum import IntEnum
# from generate_ir import generate_ir

"""
Instructions:

      NOP: xxxxxx00
           pc <- pc + 1
Increment: xxxxxx01
           counter <- counter + 1
           pc <- pc + 1
Decrement: xxxxxx10
           counter <- counter - 1
           pc <- pc + 1
     Jump: xxxxxx11
           pc <- pc + xxxxxx
"""

WIDTH = 8

class OP(IntEnum):
    NOP  = 0x0
    INC  = 0x1
    DEC  = 0x2
    JUMP = 0x3

# Declarations:
# -------------

# Stall input - if high, propagate NOP through pipeline
# stall = pyrtl.Input(1, 'stall')

# Program counter
pc = pyrtl.Register(WIDTH, 'pc')

# Instruction memory
imem = pyrtl.MemBlock(bitwidth=WIDTH, addrwidth=WIDTH, name='imem')

# Data counter
counter = pyrtl.Register(WIDTH, 'counter')

# Pipeline registers:
#   `d_` and `x_` indicate which stage the registers are used
#   (`d` for decode, `x` for execute)
d_inst = pyrtl.Register(WIDTH, 'd_inst')
d_pc = pyrtl.Register(WIDTH, 'd_pc')

# Wire to hold ALU result
alu_result = pyrtl.WireVector(WIDTH, 'alu_out')

# Stage 1: Fetch
# --------------
branch_taken = pyrtl.WireVector(1, 'branch_taken')
branch_target = pyrtl.WireVector(WIDTH, 'branch_target')

# Read from instruction memory at current PC
# Store fetched instruction in instruction register
# Will be available in the *next* cycle
with pyrtl.conditional_assignment:
    with branch_taken:
        d_inst.next |= 0x00 # NOP
    with pyrtl.otherwise:
        d_inst.next |= imem[pc]

# Increment PC
# `|=` is PyRTL's "conditional assignment" operator, used in `with` expressions
with pyrtl.conditional_assignment:
    # with stall:
    #     pc.next |= pc
    with branch_taken:
        pc.next |= branch_target
    with pyrtl.otherwise:
        pc.next |= pc + 1

d_pc.next <<= pc

# Stage 2: Decode + Execute
# ---------------
inst_op = pyrtl.WireVector(2, 'inst_op')
inst_imm = pyrtl.WireVector(8, 'inst_imm')
inst_op <<= d_inst[WIDTH-2:WIDTH]
inst_imm <<= d_inst[0:WIDTH-2].sign_extended(WIDTH)

# Control signals
# ctrl_branch = pyrtl.WireVector(1, 'ctrl_branch')
# ctrl_write = pyrtl.WireVector(1, 'ctrl_write')

# Control logic
# ctrl_branch <<= pyrtl.net_hole('ctrl_branch', 1, inst_op)
# ctrl_write <<= pyrtl.net_hole('ctrl_write', 1, inst_op)

alu_result <<= pyrtl.enum_mux(
        inst_op,
        {
            OP.INC: counter + 1,
            OP.DEC: counter - 1,
            OP.JUMP: d_pc + inst_imm,
        },
        default=0)

with pyrtl.conditional_assignment:
    with inst_op == OP.JUMP:
        branch_taken |= 1
        branch_target |= alu_result

with pyrtl.conditional_assignment:
    with (inst_op != OP.JUMP) & (inst_op != OP.NOP):
        counter.next |= alu_result

# -------------------------------------------------------------------------------

# pyrtl.optimize()
# ir = generate_ir('pipelined-counter', pyrtl.working_block())
# print(ir)

# Start a simulation
sim_trace = pyrtl.SimulationTrace()

imem_init = {
    0: int('01000000', 2),
    1: int('01000000', 2),
    2: int('01000000', 2),
    3: int('10000000', 2),
    4: int('11000011', 2),
    5: int('10000000', 2),
    6: int('10000000', 2),
    7: int('01000000', 2),
    8: int('01000000', 2),
    9: int('01000000', 2),
   10: int('00000000', 2),
}

sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
    imem : imem_init,
})

# Run
for i in range(11):
    sim.step({})

sim_trace.render_trace(symbol_len=10, segment_size=1)
