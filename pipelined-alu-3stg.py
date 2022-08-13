import pyrtl
from enum import IntEnum

class ALUOp(IntEnum):
    ADD = 0x0
    SUB = 0x1
    XOR = 0x2
    AND = 0x3
    OR  = 0x4

# Declarations:
# -------------

# Stall - if high, propagate NOP through pipeline
stall = pyrtl.Input(1, 'stall')
# "Fetch" - input to design each step is a 16-bit instruction
# If stall is high, instruction input is ignored
inst = pyrtl.Input(16, 'inst')

# Register file is a memory mapping 4-bit address to 16-bit data value
rf = pyrtl.MemBlock(bitwidth=16, addrwidth=4, name='rf')

# ALU registers for inputs and result
in1 = pyrtl.Register(16, 'in1')
in2 = pyrtl.Register(16, 'in2')
out = pyrtl.Register(16, 'out')
alu_result = pyrtl.WireVector(16, 'alu_out')

# Pipeline registers
c_addr_1 = pyrtl.Register(4, 'c_addr_1')
c_addr_2 = pyrtl.Register(4, 'c_addr_2')
op_1 = pyrtl.Register(4, 'op_1')
write_1 = pyrtl.Register(1, 'write_1')
write_2 = pyrtl.Register(1, 'write_2')

# Stage 0:
# -------------------

# Decode instruction:
# opcode, two source registers (a, b), destination register (c)
inst_a = inst[0:4]
inst_b = inst[4:8]
inst_c = inst[8:12]
inst_op = inst[12:16]

# In next cycle, op_1 gets updated with inst_op
op_1.next <<= inst_op

# Read from register file and do register forwarding
with pyrtl.conditional_assignment:
    with stall:
        in1.next |= 0
    with c_addr_1 == inst_a:
        in1.next |= alu_result
    with c_addr_2 == inst_a:
        in1.next |= out
    with pyrtl.otherwise:
        in1.next |= rf[inst_a]

with pyrtl.conditional_assignment:
    with stall:
        in2.next |= 0
    with c_addr_1 == inst_b:
        in2.next |= alu_result
    with c_addr_2 == inst_b:
        in2.next |= out
    with pyrtl.otherwise:
        in2.next |= rf[inst_b]

with pyrtl.conditional_assignment:
    with stall:
        write_1.next |= 0
        c_addr_1.next |= 0
    with pyrtl.otherwise:
        write_1.next |= 1
        c_addr_1.next |= inst_c

# Stage 1:
# -------------------
# Perform ALU operation
alu_result <<= pyrtl.enum_mux(
        op_1,
        {
            ALUOp.ADD: in1 + in2,
            ALUOp.SUB: in1 - in2,
            ALUOp.XOR: in1 ^ in2,
            ALUOp.OR: in1 | in2,
            ALUOp.AND: in1 & in2,
        },
        default=0)

out.next <<= alu_result

write_2.next <<= write_1
c_addr_2.next <<= c_addr_1

# Stage 2:
# -------------------
# Write result back to register file
rf[c_addr_2] <<= pyrtl.MemBlock.EnabledWrite(out, write_2)

# ------------------------------------------------------------------------------

# Start a simulation
sim_trace = pyrtl.SimulationTrace()

# Initialize reg file
rf_init = {}
for i in range(16):
    rf_init[i] = i

sim = pyrtl.Simulation(tracer=sim_trace, memory_value_map={
    rf : rf_init,
})

# Run
sim.step({'inst': 0x0112, 'stall': 0})
sim.step({'inst': 0x0333, 'stall': 0})
sim.step({'inst': 0x1221, 'stall': 0})
sim.step({'inst': 0x1121, 'stall': 0})
sim.step({'inst': 0x0000, 'stall': 1})
sim.step({'inst': 0x0000, 'stall': 1})

sim_trace.render_trace(symbol_len=10, segment_size=1)

# Print out the register file
print(sim.inspect_mem(rf))
