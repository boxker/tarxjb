import hashlib
import os

import paramiko as pm

# name:tarxjb
# author:boxker
# mail:icjb@foxmail.com
# need only paramiko
# python version > 3.4
# Used to copy files

log_flag = True


def create_ssh(host):
    # 创建ssh链接
    ssh = pm.SSHClient()
    ssh.set_missing_host_key_policy(pm.AutoAddPolicy())
    ssh.connect(hostname=host["ip"], port=host["port"],
                username=host["username"], password=host["password"])
    return ssh


def create_sftp(host):
    # 创建sftp链接
    trans = pm.Transport((host["ip"], host["port"]))
    trans.connect(username=host["username"], password=host["password"])
    sftp = pm.SFTPClient.from_transport(trans)
    return sftp


def exist_file(ssh, file):
    # 判断文件是否存在
    cmd = "find {file}".format(file=file)
    return exe_cmd(ssh, cmd)


def del_file(ssh, file):
    # 删除文件
    cmd = "rm -rf {file}".format(file=file)
    return exe_cmd(ssh, cmd)


def tar_file(ssh, file, typ="c", compress=True, pk_name=".tarxjb"):
    # 打包压缩
    gzip = "z"
    if not compress:
        gzip = ""
    cmd = "tar {typ}{gzip}vfpP {file}{pk_name} {file}".format(typ=typ, gzip=gzip, file=file, pk_name=pk_name)
    if typ != "c":
        typ = "x"
        cmd = "tar {typ}{gzip}vfpP {file}{pk_name}".format(typ=typ, gzip=gzip, file=file, pk_name=pk_name)
    return exe_cmd(ssh, cmd)


def mv_file(ssh, ofile, nfile):
    # 移动文件、改名
    cmd = "mv {ofile} {nfile}".format(ofile=ofile, nfile=nfile)
    return exe_cmd(ssh, cmd)


def cp_file(ssh, ofile, nfile):
    # 复制文件
    cmd = "cp {ofile} {nfile}".format(ofile=ofile, nfile=nfile)
    return exe_cmd(ssh, cmd)


def md5_file(ssh, file):
    # 计算md5
    cmd = "md5sum {file} | awk \'{{print $1}}\'".format(file=file)
    return exe_cmd(ssh, cmd)


def exe_cmd(ssh, cmd):
    # 执行命令
    _, sout, serr = ssh.exec_command(cmd)
    out = sout.read().decode()
    err = serr.read().decode()
    if err != "":
        log_print(err)
        return False, err
    log_print(out)
    return True, out


def exe_cmd_in(ssh, cmd):
    # 执行命令,返回所有参数
    sin, sout, serr = ssh.exec_command(cmd)
    out = sout.read().decode()
    err = serr.read().decode()
    if err != "":
        log_print(err)
        return False, sin, sout, serr
    log_print(out)
    return True, sin, sout, serr


def log_print(s, flag=None):
    # 打印日志
    if flag is None:
        flag = log_flag
    if flag:
        print("->" + str(s))


def transfer_get(sftp, file, nfile, md5=None):
    # 下载文件
    for count in range(5):
        sftp.get(file, nfile)
        if os.path.exists(nfile):
            if md5 is None:
                return True
            m = hashlib.md5()
            with open(nfile, mode="rb") as f:
                fr = f.read()
            m.update(fr)
            m_new = m.hexdigest()
            if m_new != md5:
                continue
            return True
    if not os.path.exists(nfile):
        return False


def transfer_put(sftp, file, nfile):
    # 上传文件
    if not os.path.exists(nfile):
        return False
    sftp.put(file, nfile)
    return True

# sftp = create_sftp({
#     "ip": "10.112.98.132",
#     "port": 22,
#     "username": "root",
#     "password": "111",
#     "file": "/root/111.o"
# })
# ssh = create_ssh({
#     "ip": "10.112.98.132",
#     "port": 22,
#     "username": "root",
#     "password": "111",
#     "file": "/root/111.o"
# })

# transfer_get(sftp, "/root/111.o", "111.o", "d00dc160af12d3d6b4a63095ab4d7550")

# tf, out = md5_file(ssh, "/root/111.o")
# print(tf)
# print(out)
# print(md5_file(ssh, "/root/111.o"))
# print(sftp.stat("/root/111.o"))
# print(tar_file(ssh, "/root/111.o"))
# sftp.get("/root/111.o", "./111.o")
# print(mv_file(ssh, "/root/111.o", "/root/222.o"))
