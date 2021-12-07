import sys

arglut = [
    'rd',
    'rt',
    'rs1',
    'rs2',
    'rs3',
    'imm2',
    'imm3',
    'imm4',
    'imm5',
    'imm6',
]

arg_priority = {
    'rd': 0,
    'rt': 0,
    'rs1': 1,
    'rs2': 2,
    'rs3': 3,
    'imm2': 4,
    'imm3': 4,
    'imm4': 4,
    'imm5': 4,
    'imm6': 4,
}

arg_type_map = {
    'rd': 'regidx',
    'rt': 'regidx',
    'rs1': 'regidx',
    'rs2': 'regidx',
    'rs3': 'regidx',
    'imm2': 'bits(2)',
    'imm3': 'bits(3)',
    'imm4': 'bits(4)',
    'imm5': 'bits(5)',
    'imm6': 'bits(6)',
}

arg_assembly_map = {
    'rd': 'reg_name(rd)',
    'rt': 'reg_name(rt)',
    'rs1': 'reg_name(rs1)',
    'rs2': 'reg_name(rs2)',
    'rs3': 'reg_name(rs3)',
    'imm2': 'hex_bits_2(imm2)',
    'imm3': 'hex_bits_3(imm3)',
    'imm4': 'hex_bits_4(imm4)',
    'imm5': 'hex_bits_5(imm5)',
    'imm6': 'hex_bits_6(imm6)',
}

p_inst_table = {}

for line in sys.stdin:
    entries = line.split()
    name = entries[0]
    name = name.replace(".", "_").upper()
    entries = entries[1:]
    entries = [entry.split('=')[-1] for entry in entries]

    args = [entry for entry in entries if entry in arglut]
    args_tuple = tuple(args)

    if (args_tuple not in p_inst_table):
        p_inst_table[args_tuple] = []
    
    p_inst_table[args_tuple].append({
        'name': name,
        'entries': entries,
    })

# # riscv_types.sail
# print('/* riscv_types.sail */')
# print()
# for args, p_insts in p_inst_table.items():
#     names = [p_inst['name'] for p_inst in p_insts]
#     token = f"p_inst_{'_'.join(args)}"

#     # example:
#     # enum p_inst_rs2_rs1_rd_op = {ADD8, ADD16, ADD64, ...}
#     print(f"enum {token}_op = {{{', '.join(names)}}}")
# print()

# # riscv_pext_tmp_function.sail
# print("/* riscv_pext_tmp_function.sail */")
# print()
# for args, p_insts in p_inst_table.items():
#     arg_types = [arg_type_map[arg] for arg in args]
#     arg_list = ', '.join(args)
#     # example:
#     # val PEXT_ADD8 : (regidx, regidx, regidx) -> bits(1)
#     # function PEXT_ADD8(rs2, rs1, rd) = 0b0
#     # val PEXT_ADD16 : (regidx, regidx, regidx) -> bits(1)
#     # function PEXT_ADD16(rs2, rs1, rd) = 0b0
#     # ...
#     for p_inst in p_insts:
#         name = p_inst['name']
#         print(f"val PEXT_{name} : ({', '.join(arg_types)}) -> bits(1)")
#         print(f"function PEXT_{name}({arg_list}) = 0b0")
#         print()



# riscv_insts_pext_define.sail
print('/* riscv_insts_pext_define.sail */')

for args, p_insts in p_inst_table.items():
    names = [p_inst['name'] for p_inst in p_insts]
    token = f"p_inst_{'_'.join(args)}"
    arg_types = [arg_type_map[arg] for arg in args]
    arg_assembly = [arg_assembly_map[arg] for arg in sorted(args, key=lambda arg: arg_priority[arg])]
    arg_list = ', '.join(args)
    # example:
    # mapping p_inst_rs2_rs1_rd_mapping : p_inst_rs2_rs1_rd_op <-> string = {
    #     ADD8 <->  "ADD8",
    #     ADD16 <->  "ADD16",
    #     ADD64 <->  "ADD64",
    #     ...
    # }
    print()
    print(f"mapping {token}_mapping : {token}_op <-> string = {{")
    print(",\n".join([fR'  {name} <-> "{name}"' for name in names]))
    print("}\n")

    # example:
    # union clause ast = P_INST_RS2_RS1_RD : (regidx, regidx, regidx, p_inst_rs2_rs1_rd_op)
    print(f"union clause ast = {token.upper()} : ({', '.join(arg_types)}, {token}_op)")
    # example:
    # mapping clause encdec = PEXT_ADD8 (rs2, rs1, rd) <->
    # 0b0100100 @ rs2 @ rs1 @ 0b000 @ rd @ 0b1110111
    # mapping clause encdec = PEXT_ADD16 (rs2, rs1, rd) <->
    # 0b0100000 @ rs2 @ rs1 @ 0b000 @ rd @ 0b1110111
    # ...
    for p_inst in p_insts:
        name = p_inst['name']
        entries = p_inst['entries']
        print(f"mapping clause encdec = {token.upper()}({arg_list}, {name}) <->")
        print(f"  {' @ '.join(entries)}")


    # example:
    # mapping clause assembly = P_INST_RS2_RS1_RD (rs2, rs1, rd, p_inst)
    #   <-> p_inst_rs2_rs1_rd_mapping(p_inst) ^ spc() ^ reg_name(rd) ^ sep() ^ reg_name(rs1) ^ sep() ^ reg_name(rs2)
    print()
    print(f"mapping clause assembly = {token.upper()}({arg_list}, p_inst)")
    print(f"  <-> {token}_mapping(p_inst) ^ spc() ^ {' ^ sep() ^ '.join(arg_assembly)}")

    # example
    # function clause execute (P_INST_RS2_RS1_RD(rs2, rs1, rd, p_inst)) = {
    #   let result : bits(1) = match p_inst {
    #     ADD8 => PEXT_ADD8(rs2, rs1, rd),
    #     ADD16 => PEXT_ADD16(rs2, rs1, rd),
    #     ADD64 => PEXT_ADD64(rs2, rs1, rd),
    #     ...
    #   };
    #   RETIRE_SUCCESS;
    # }
    print()
    print(f"function clause execute ({token.upper()}({arg_list}, p_inst)) = {{")
    print(f"  let success : bool = match p_inst {{")
    print(",\n".join([f'    {name} => PEXT_{name}({arg_list})' for name in names]))
    print("  };")
    print("  if success then \n\
    RETIRE_SUCCESS\n\
  else {\n\
    handle_illegal();\n\
    RETIRE_FAIL\n\
  }")
    print("}")
