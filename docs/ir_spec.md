# MiniCompiler Intermediate Representation (IR) Specification

**Version:** 1.0  
**Status:** Stable (Sprint 4)  
**Target:** Platform-independent Three-Address Code

---

## 1. Overview

The MiniCompiler IR is a typed, three-address code representation designed to bridge the gap between the decorated Abstract Syntax Tree (AST) and target code generation. It is structured around **Basic Blocks** and a **Control Flow Graph (CFG)**, making it suitable for optimization passes and backend lowering.

### Design Principles
- **Three-Address Code:** Every computation instruction produces at most one result.
- **Explicit Control Flow:** No implicit fall-through between unrelated blocks; all branches are explicit `JUMP` instructions.
- **SSA-Ready:** Uses virtual registers (`t1`, `t2`, ...) for intermediate values, facilitating future SSA transformation.
- **Deterministic:** Block ordering and instruction layout are stable across runs for reproducible testing.

---

## 2. Core Concepts

### 2.1 Operands
| Type | Syntax | Description |
|------|--------|-------------|
| Temporary | `tN` | Virtual register for intermediate results (`t1`, `t2`, ...) |
| Variable | `name` | Source-level named variable or parameter |
| Literal | `42`, `3.14`, `true`, `"str"` | Constant value with inferred type |
| Label | `L_name` | Identifier for a Basic Block |
| Memory | `[base]` or `[base+offset]` | Dereferenced address for load/store operations |

### 2.2 Basic Blocks
A Basic Block is a sequence of instructions with:
- **Single entry point:** Marked by a `LABEL`.
- **Single exit point:** Ends with a terminator (`JUMP`, `JUMP_IF`, `JUMP_IF_NOT`, or `RETURN`).
- **Linear execution:** No internal branches or jumps.

### 2.3 Control Flow Graph (CFG)
- Nodes are Basic Blocks.
- Edges represent possible control transfers.
- Every function has an `entry` block.
- Unreachable blocks are preserved but listed after reachable ones.

---

## 3. Instruction Set

Instructions are categorized by operation type. All computation instructions follow the `dest = OP src1, src2` pattern.

### 3.1 Arithmetic
| Instruction | Format | Description |
|-------------|--------|-------------|
| `ADD` | `tD = ADD tA, tB` | Integer/Float addition |
| `SUB` | `tD = SUB tA, tB` | Subtraction |
| `MUL` | `tD = MUL tA, tB` | Multiplication |
| `DIV` | `tD = DIV tA, tB` | Division |
| `MOD` | `tD = MOD tA, tB` | Modulo |
| `NEG` | `tD = NEG tA` | Unary negation |

### 3.2 Comparison
| Instruction | Format | Description |
|-------------|--------|-------------|
| `CMP_EQ` | `tD = CMP_EQ tA, tB` | Equal |
| `CMP_NE` | `tD = CMP_NE tA, tB` | Not equal |
| `CMP_LT` | `tD = CMP_LT tA, tB` | Less than |
| `CMP_LE` | `tD = CMP_LE tA, tB` | Less or equal |
| `CMP_GT` | `tD = CMP_GT tA, tB` | Greater than |
| `CMP_GE` | `tD = CMP_GE tA, tB` | Greater or equal |

*Note: All comparison instructions produce a boolean result.*

### 3.3 Logical
| Instruction | Format | Description |
|-------------|--------|-------------|
| `AND` | `tD = AND tA, tB` | Logical AND |
| `OR`  | `tD = OR tA, tB`  | Logical OR |
| `NOT` | `tD = NOT tA`     | Logical NOT |
| `XOR` | `tD = XOR tA, tB` | Bitwise/Logical XOR |

### 3.4 Memory
| Instruction | Format | Description |
|-------------|--------|-------------|
| `ALLOCA` | `tD = ALLOCA size` | Allocate stack memory (bytes) |
| `LOAD`   | `tD = LOAD [addr]` | Read from memory |
| `STORE`  | `STORE [addr], tS` | Write to memory |

### 3.5 Control Flow
| Instruction | Format | Description |
|-------------|--------|-------------|
| `JUMP`      | `JUMP L_target` | Unconditional branch |
| `JUMP_IF`   | `JUMP_IF tCond, L_target` | Branch if `tCond != 0` |
| `JUMP_IF_NOT`| `JUMP_IF_NOT tCond, L_target` | Branch if `tCond == 0` |

### 3.6 Functions
| Instruction | Format | Description |
|-------------|--------|-------------|
| `CALL`  | `tD = CALL fname(args...)` | Invoke function |
| `RETURN`| `RETURN [val]` | Exit function (optional value) |
| `PARAM` | `PARAM idx, val` | Pass argument (lowered from CALL) |

---

## 4. Textual IR Syntax

The IR serializer follows strict formatting rules for readability and machine parsing:

```text
function <name>: <return_type> (<param_type> <param_name>, ...)
  <label>:
    <4-space indent><instruction>  # <optional comment>
    <4-space indent><instruction>
    ...
    <4-space indent><terminator>
```
