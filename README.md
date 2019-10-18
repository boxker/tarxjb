# tarxjb
easy remote copy file tool by python


# tarxjb 简单、安全文件拷贝、传输

## 描述

通过python paramiko库实现简易ssh、sftp执行操作，从而实现文件的远程传输

[Github](https://github.com/boxker/tarxjb.git "Github")

## 优点：

- 可靠传输，文件不易受损
- 安全传输，避免文件丢失、覆盖
- 节省带宽，压缩传输

## 缺点

- 需要本地中转，对于带宽资源较少的服务器压力大
- 需要计算md5及解压缩，对cpu占用大
- 强制退出会失败

## 详细过程

### 源主机

1. 检查文件/目录是否存在
2. 打包（压缩）
3. 计算md5
4. 保存到本地

### 目的主机

1. 判断是否存在同名文件
2. 上传文件
3. 计算md5
4. 解包

