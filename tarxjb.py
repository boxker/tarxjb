import os
import time
import threading

import ssh_cmd as sc

# name:tarxjb
# author:boxker
# mail:icjb@foxmail.com
# need only paramiko
# python version > 3.4
# Used to copy files

# 默认运行配置：源
example_src = {
    "ip": "10.112.98.132",
    "port": 22,
    "username": "root",
    "password": "111",
    "file": "/root/111.o"
}

# 默认运行配置：目的，数组
example_dst = [
    {
        "ip": "10.112.98.134",
        "port": 22,
        "username": "root",
        "password": "222",
        "file": "/root/222.o"
    },
    {
        "ip": "10.112.98.151",
        "port": 22,
        "username": "root",
        "password": "333",
        "file": "/root/333.o"
    },
    {
        "ip": "10.112.96.67",
        "port": 22,
        "username": "root",
        "password": "444",
        "file": "/root/111.o"
    }
]


def copy(src_host, dst, compress=True, force=False):
    # 存储结果、线程
    threads = []
    result = []
    # 创建源ssh
    src_ssh = sc.create_ssh(src_host)
    # 判断源文件是否存在
    tf, out = sc.exist_file(src_ssh, src_host["file"])
    if not tf:
        src_ssh.close()
        return False, None
    # 包后缀名
    pkname = ".{time}.tarxjb".format(time=str(int(time.time())))
    # 打包文件
    tf, out = sc.tar_file(src_ssh, src_host["file"], pk_name=pkname, compress=True)
    if not tf:
        src_ssh.close()
        return False, None
    # 计算md5
    tf, src_md5 = sc.md5_file(src_ssh, src_host["file"] + pkname)
    if not tf:
        src_ssh.close()
        return False, None
    # 本地临时文件名
    temp_file = "./temp" + pkname
    # 下载文件
    src_sftp = sc.create_sftp(src_host)
    # if not sc.transfer_get(src_sftp, src_host["file"] + pkname, temp_file, src_md5):
    if not sc.transfer_get(src_sftp, src_host["file"] + pkname, temp_file):
        return False, None
    src_sftp.close()
    # 删除源主机打包产生的临时文件
    tf, out = sc.del_file(src_ssh, src_host["file"] + pkname)
    if not tf:
        src_ssh.close()
        return False, None
    src_ssh.close()
    # 上传文件
    for one in dst:
        # 单线程执行
        # copy_one(src_ssh, one, src_file=src_host["file"], temp_file=temp_file, pk_name=pkname, src_md5=src_md5)
        # 多线程执行
        t = threading.Thread(target=thread_run,
                             args=(result, src_ssh, one, src_host["file"], temp_file, pkname, src_md5, compress, force))
        t.start()
        threads.append(t)
    # 等待所有线程执行结束
    for t in threads:
        t.join()
    # 删除本地临时文件
    os.remove(temp_file)
    return True, result


def thread_run(result, src_ssh, one, src_file, temp_file, pk_name, src_md5, compress=True, force=False):
    ret = copy_one(src_ssh, one, src_file=src_file, temp_file=temp_file, pk_name=pk_name, src_md5=src_md5,
                   compress=compress, force=force)
    result.append({
        "ip": one["ip"],
        "file": one["file"],
        "result": ret
    })


def copy_one(src_ssh, dst_host, src_file, temp_file, pk_name=".tarxjb", src_md5=None, compress=True, force=False):
    # copy单个文件至目的主机
    dst_ssh = sc.create_ssh(dst_host)
    dst_sftp = sc.create_sftp(dst_host)
    now = "tarxjb" + str(int(time.time()))
    # 判断目的主机是否存在名字冲突的文件，存在则自动备份，文件处理结束后再恢复
    other_conflict = False
    if src_file != dst_host["file"]:
        tf, out = sc.exist_file(dst_ssh, src_file)
        if tf == True:
            sc.log_print("backup other")
            sc.mv_file(dst_ssh, src_file, src_file + now)
            other_conflict = True
    # 判断目的主机是否存在同名文件
    tf, out = sc.exist_file(dst_ssh, dst_host["file"])
    sc.log_print("exist: " + str(tf))
    if tf:
        if not force:
            # 备份同名文件
            sc.log_print("backup file")
            sc.mv_file(dst_ssh, dst_host["file"],
                       dst_host["file"] + ".{time}.bakcup".format(time=now))
    # 上传文件
    tf = sc.transfer_put(dst_sftp, temp_file, temp_file)
    if not tf:
        dst_ssh.close()
        dst_sftp.close()
        return False
    # 检查文件是否上传成功
    tf, out = sc.exist_file(dst_ssh, temp_file)
    if not tf:
        dst_ssh.close()
        dst_sftp.close()
        return False
    # 修改临时文件名称
    tf, out = sc.mv_file(dst_ssh, temp_file, src_file + pk_name)
    if not tf:
        dst_ssh.close()
        dst_sftp.close()
        return False
    # 计算包md5
    if src_md5 is not None:
        tf, dst_md5 = sc.md5_file(dst_ssh, src_file + pk_name)
        if dst_md5 != src_md5:
            return False
    # 解包
    tf, out = sc.tar_file(dst_ssh, src_file, typ="x", pk_name=pk_name, compress=compress)
    if not tf:
        dst_ssh.close()
        dst_sftp.close()
        return False
    # 删除临时文件
    tf, out = sc.del_file(dst_ssh, src_file + pk_name)
    if not tf:
        dst_ssh.close()
        dst_sftp.close()
        return False
    # 改名
    if src_file != dst_host["file"]:
        tf, out = sc.mv_file(dst_ssh, src_file, dst_host["file"])
        if not tf:
            # 改名失败，移除
            sc.del_file(dst_ssh, src_file)
            dst_ssh.close()
            dst_sftp.close()
            return False
    # 如果前面有备份可能冲突的文件，现在恢复
    if other_conflict:
        sc.log_print("other back")
        sc.mv_file(dst_ssh, src_file + now, src_file)
    dst_ssh.close()
    dst_sftp.close()
    return True


if __name__ == "__main__":
    print("easy copy")
    # 是否显示完整日志
    sc.log_flag = False
    log_level = input("show detail?(default: n)please input y or n->")
    if log_level == "y":
        sc.log_flag = True
    # 是否压缩
    compress_str = input("compress?(default: y)please input y or n->")
    compress = True
    if compress_str == "n":
        compress = False
    print("compress: " + str(compress))
    # 是否强制覆盖
    force_str = input("force?(default: n)please input y or n->")
    force = False
    if force_str == "y":
        force = True
    print("force: " + str(force))
    # 输入源信息
    print("ip:port:username:password:file")
    print("please input src(default:port:22)")
    src_str = input("input->")
    src_list = src_str.split(":")
    # 格式错误处理
    if len(src_list) != 5:
        print("format error")
        exit(0)
    if src_list[1] == "":
        src_list[1] = 22
    src_host = {
        "ip": src_list[0],
        "port": int(src_list[1]),
        "username": src_list[2],
        "password": src_list[3],
        "file": src_list[4]
    }
    # 输入目的信息
    dst = []
    while True:
        print("please input dst(default:port:22,username:src username,password:src password,file:src file),quit:q")
        dst_str = input("input->")
        if dst_str == "":
            continue
        dst_list = dst_str.split(":")
        if dst_str[0] == "q":
            break
        if len(dst_list) != 5:
            print("format error")
            continue
        if dst_list[1] == "":
            dst_list[1] = 22
        if dst_list[2] == "":
            dst_list[2] = src_host["username"]
        if dst_list[3] == "":
            dst_list[3] = src_host["password"]
        if dst_list[4] == "":
            dst_list[4] = src_host["file"]
        dst_host = {
            "ip": dst_list[0],
            "port": int(dst_list[1]),
            "username": dst_list[2],
            "password": dst_list[3],
            "file": dst_list[4]
        }
        dst.append(dst_host)
    sc.log_print("src: " + str(src_host))
    sc.log_print("dst: " + str(dst))
    if len(dst) == 0:
        exit(0)
    print("->processing...")
    # 执行拷贝操作
    tf, res = copy(src_host, dst, compress=compress, force=force)
    # print("->res: " + str(res))
    if res is None:
        print("error,please check or show more info")
        exit(0)
    print("->res:")
    for row in res:
        print("->ip:{ip} file:{file} res:{result}".format(ip=row["ip"], file=row["file"], result=row["result"]))

    # 使用示例
    # print(copy(example_src, example_dst, compress=True, force=False))
    # 10.112.98.132:22:root:111:/root/111.o

    # 10.112.98.134:22:root:222:/root/111.o
    # 10.112.98.151:22:root:333:/root/111.o
    # 10.112.96.67:22:root:444:/root/111.o
