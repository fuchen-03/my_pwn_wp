## 栈迁移带画图解释

**栈迁移一直是我不擅长的方法，这次用画图的形式来倒着解释exp，然后再利用画图解释如何栈偏移的思路**

```python
 b'\x00'*[buf]+flat(bss,read_addr)
```

这个payload构造使得<font color ="red">`rbp = bss,ret_addr=read_addr`</font>，现将`bss`段地址写入`rbp`中，然后返回到`read`函数继续覆写rbp。

![](https://github.com/GUANZH1/my_pwn_wp/raw/main/stack%20pivoting/pl1.png)

<font color ="gree">首先，在返回到read函数时，`rbp=bss`，`rdi=rbp-[buf]=bss-0x100`</font>

```python
flat(bss+0x200, pop_rdi,elf.got['puts'],elf.plt['puts'],read_addr).ljust(buf,b'\x00')+flat(bss-[buf],leave_ret)
```

这段payload构造`bss-[buf]`开始写入数据，先写入了<font color ="red">`bss+0x200`（写啥都无所谓，0x200,0x300都行）</font>，然后把`leak`链也构造完成。最后在`rbp`位置上填入`bss-[buf]`，在`ret`位置上填入`leave_ret`，构造出了<font color ="yellow">`bss->bss-[buf]->bss+0x200`</font>， 而且此次构造有两次leave ret指令，第一次执行使得<font color ="red">`rbp=bss-[buf]->buf+0x200,rsp=bss+0x8`</font>，第二次执行使得<font color ="red">`rbp=buf+0x200,rsp=bss-[buf]+x8`</font>，根据这一步从而泄露了`puts`的地址，得到`libc`基地址

![](https://github.com/GUANZH1/my_pwn_wp/raw/main/stack%20pivoting/pl2.png)

<font color ="gree">首先，在返回到read函数时，`rbp=bss+0x200`，`rdi=rbp-[buf]=bss+0x100`</font>

```python
flat(bss, ret, pop_rdi, bin_sh, libc.sym['system']).ljust(buf,b'\x00')+flat(bss+0x200-[buf],leave_ret)
```

在得到基地址之后先找到`str_bin_sh`的地址和`system`的地址，方便后面调用。这段payload构造了`system("/bin/sh")`，在`rbp`上填入`bss+0x200-[buf]==rdi`，方法同上，不过多叙述。

![](https://github.com/GUANZH1/my_pwn_wp/raw/main/stack%20pivoting/pl3.png)