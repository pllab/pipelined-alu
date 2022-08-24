# Pipelined ALU

This document describes the design of a 3-stage pipelined ALU with an
unconditional branch instruction.

## Instruction set

There are five register-to-register instructions and one unconditional branch
instruction.

- Register instructions have the following format:
  - `op rd rs2 rs1` which updates register `rd` with the result of apply the
  operator `op` over source registers `rs1` and `rs2`.
      - `ADD rd rs2 rs1`
      - `SUB rd rs2 rs1`
      - `XOR rd rs2 rs1`
      - `AND rd rs2 rs1`
      - `OR rd rs2 rs1`
- Unconditional branch:
  - `JUMP immediate` which updates the program counter by adding the current
    program counter with the `immediate` value.

### State

There are three pieces of state at the instruction set architecture level:

1. Program counter (PC): A 16-bit register.
2. Register file: A memory containing 16 cells for storing 16-bit registers.
3. Instruction memory: A memory mapping 16-bit addresses to 16-bit values.

## Microarchitecture

The following diagram depicts the overall microarchitecture for this processor:

The pipeline for this design consists of three stages:

1. Instruction fetch:
   - Read from instruction memory at the address denoted by the current PC
   value.
   - Store the read instruction into a pipeline register for use in the next
   stage. If a branch is being taken, replace this instruction with a NOP.
   - Update the PC: If there is a stall signal, do not update the PC. If a
     branch is being taken, update the PC to be the calculated branch target.
     Otherwise, increment the PC by 1.
2. Instruction decode:
   - Decode the instruction from the instruction register into its separate
     parts for opcode, destination register, source registers, and immediate
     value.
   - Set control signals based on the instruction opcode.
   - Prepare the inputs for the ALU operation in the next stage.
     - ALU input 1: If the instruction is a branch, then set this input to be
       the PC. If the register being used here is being _written to_ then
       forward the result of the ALU directly here (instead of waiting a cycle
       for the register file to be written to). Otherwise, read from the
       register file the register specified by the instruction.
     - ALU input 2: Follows similarly, but if the instruction is a branch then
       set this input to be the immediate value computed from the instruction.
3. Execute and register file write-back:
   - Perform the ALU operation based on the ALU input and op registers.
   - If a branch is being taken, forward the branch target to the PC update
     stage.
   - If the instruction is a register operation, write the ALU result back to
     the register file.

## Implementation notes

## To run

1. Install [PyRTL](https://ucsbarchlab.github.io/PyRTL/).
   - Should just be `pip3 install pyrtl` or `pip install pyrtl`.
2. Run with: `python pipelined-alu.py`
