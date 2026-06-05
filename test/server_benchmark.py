#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux服务器性能测试脚本
测试内容：CPU、GPU、内存、硬盘、网卡
"""

import paramiko
import time
import json
import sys

HOST = "192.168.0.214"
USER = "user"
PASS = "Aa123"
PORT = 22

results = {}

def run_cmd(ssh, cmd, timeout=120):
    """执行命令并返回输出"""
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        return out.strip(), err.strip()
    except Exception as e:
        return "", str(e)

def connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    print(f"[OK] 成功连接到 {HOST}")
    return ssh

def test_system_info(ssh):
    print("\n========== 系统基本信息 ==========")
    out, _ = run_cmd(ssh, "uname -a")
    print(f"内核: {out}")
    
    out, _ = run_cmd(ssh, "cat /etc/os-release 2>/dev/null | head -5")
    print(f"OS信息:\n{out}")
    
    results['system'] = {'kernel': out}

def test_cpu(ssh):
    print("\n========== CPU 性能测试 ==========")
    
    # CPU基本信息
    out, _ = run_cmd(ssh, "lscpu | grep -E 'Model name|Architecture|CPU\\(s\\)|Thread|Core|Socket|MHz|Cache'")
    print(f"[CPU信息]\n{out}")
    results['cpu'] = {'info': out}
    
    # 安装sysbench（如果没有）
    print("[*] 检查 sysbench...")
    out, _ = run_cmd(ssh, "which sysbench 2>/dev/null && echo 'found' || echo 'not found'")
    
    if 'not found' in out:
        print("[*] 安装 sysbench...")
        out, err = run_cmd(ssh, "sudo apt-get install -y sysbench 2>&1 || sudo yum install -y sysbench 2>&1", timeout=120)
        print(f"安装结果: {out[:200] if out else err[:200]}")
    
    # CPU sysbench测试（单线程）
    print("[*] 运行 CPU 单线程测试 (10秒)...")
    out, err = run_cmd(ssh, "sysbench cpu --cpu-max-prime=20000 --threads=1 --time=10 run 2>&1", timeout=60)
    if out:
        print(f"[CPU 单线程结果]\n{out}")
        results['cpu']['single_thread'] = out
    else:
        print(f"sysbench未安装，使用备用测试...")
        # 备用：用python计算密集测试
        out, _ = run_cmd(ssh, "python3 -c \"\nimport time\nstart=time.time()\nresult=sum(i*i for i in range(10000000))\nelapsed=time.time()-start\nprint(f'Python计算10M次平方: {elapsed:.3f}秒')\n\"", timeout=60)
        print(f"[CPU备用测试]\n{out}")
        results['cpu']['python_test'] = out
    
    # CPU多线程测试
    cpu_count, _ = run_cmd(ssh, "nproc")
    threads = cpu_count.strip() if cpu_count.strip().isdigit() else "4"
    print(f"[*] 运行 CPU 多线程测试 ({threads}线程, 10秒)...")
    out, err = run_cmd(ssh, f"sysbench cpu --cpu-max-prime=20000 --threads={threads} --time=10 run 2>&1", timeout=60)
    if out and 'error' not in out.lower():
        print(f"[CPU 多线程结果]\n{out}")
        results['cpu']['multi_thread'] = out
    
    # CPU当前使用率
    out, _ = run_cmd(ssh, "top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}' | head -1")
    print(f"[CPU当前使用率]: {out}%")
    results['cpu']['current_usage'] = out
    
    # CPU负载
    out, _ = run_cmd(ssh, "uptime")
    print(f"[系统负载]: {out}")
    results['cpu']['load'] = out

def test_gpu(ssh):
    print("\n========== GPU 性能测试 ==========")
    
    # NVIDIA GPU
    out, err = run_cmd(ssh, "nvidia-smi 2>&1")
    if 'NVIDIA' in out or 'GPU' in out:
        print(f"[NVIDIA GPU 信息]\n{out}")
        results['gpu'] = {'type': 'NVIDIA', 'info': out}
        
        # GPU详细信息
        out2, _ = run_cmd(ssh, "nvidia-smi --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu,clocks.current.graphics --format=csv,noheader 2>&1")
        print(f"[GPU 详细参数]: {out2}")
        results['gpu']['details'] = out2
        
        # GPU压测（使用CUDA）
        print("[*] 检查 GPU 计算能力...")
        out3, _ = run_cmd(ssh, "python3 -c \"import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())\" 2>&1")
        if 'True' in out3:
            print(f"[PyTorch CUDA]: {out3}")
            # 简单GPU压测
            gpu_bench = """
import torch, time
device = torch.device('cuda')
size = 4096
a = torch.randn(size, size, device=device)
b = torch.randn(size, size, device=device)
torch.cuda.synchronize()
start = time.time()
for _ in range(10):
    c = torch.mm(a, b)
torch.cuda.synchronize()
elapsed = time.time() - start
gflops = 10 * 2 * size**3 / elapsed / 1e9
print(f'矩阵乘法({size}x{size}) x10次: {elapsed:.3f}秒')
print(f'估算性能: {gflops:.1f} GFLOPS')
"""
            out4, _ = run_cmd(ssh, f"python3 -c \"{gpu_bench}\" 2>&1", timeout=120)
            print(f"[GPU 计算性能]\n{out4}")
            results['gpu']['benchmark'] = out4
        else:
            print(f"[GPU 状态]: {out3}")
            results['gpu']['pytorch'] = out3
    else:
        # 检查AMD GPU
        out_amd, _ = run_cmd(ssh, "rocm-smi 2>&1")
        if 'AMD' in out_amd or 'GPU' in out_amd:
            print(f"[AMD GPU 信息]\n{out_amd}")
            results['gpu'] = {'type': 'AMD', 'info': out_amd}
        else:
            # 检查lspci
            out_lspci, _ = run_cmd(ssh, "lspci | grep -iE 'vga|3d|display|nvidia|amd|intel.*graphics' 2>&1")
            print(f"[GPU 设备扫描]\n{out_lspci if out_lspci else '未检测到独立GPU'}")
            results['gpu'] = {'type': 'unknown', 'info': out_lspci or 'No GPU detected'}

def test_memory(ssh):
    print("\n========== 内存 性能测试 ==========")
    
    # 内存基本信息
    out, _ = run_cmd(ssh, "free -h")
    print(f"[内存信息]\n{out}")
    results['memory'] = {'info': out}
    
    out2, _ = run_cmd(ssh, "cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree'")
    print(f"[详细内存信息]\n{out2}")
    results['memory']['meminfo'] = out2
    
    # 内存条信息
    out3, _ = run_cmd(ssh, "sudo dmidecode -t memory 2>/dev/null | grep -E 'Size|Speed|Type|Manufacturer|Part' | grep -v 'No Module' | head -20")
    if out3:
        print(f"[内存条信息]\n{out3}")
        results['memory']['dimm'] = out3
    
    # sysbench内存测试
    print("[*] 运行内存带宽测试...")
    out4, err4 = run_cmd(ssh, "sysbench memory --memory-block-size=1M --memory-total-size=10G --memory-operation=write --threads=1 run 2>&1", timeout=120)
    if out4 and 'error' not in out4.lower()[:50]:
        print(f"[内存写入带宽]\n{out4}")
        results['memory']['write_bandwidth'] = out4
    else:
        # 备用：用dd测试内存
        print("[*] 使用备用内存测试...")
        out5, _ = run_cmd(ssh, "dd if=/dev/zero of=/dev/null bs=1M count=10240 2>&1", timeout=60)
        print(f"[内存备用测试]\n{out5}")
        results['memory']['dd_test'] = out5
    
    # 内存读取测试
    out6, err6 = run_cmd(ssh, "sysbench memory --memory-block-size=1M --memory-total-size=10G --memory-operation=read --threads=1 run 2>&1", timeout=120)
    if out6 and 'error' not in out6.lower()[:50]:
        print(f"[内存读取带宽]\n{out6}")
        results['memory']['read_bandwidth'] = out6

def test_disk(ssh):
    print("\n========== 硬盘 性能测试 ==========")
    
    # 磁盘信息
    out, _ = run_cmd(ssh, "lsblk -d -o NAME,SIZE,ROTA,TYPE,MODEL 2>/dev/null")
    print(f"[磁盘设备信息]\n{out}")
    results['disk'] = {'info': out}
    
    # df信息
    out2, _ = run_cmd(ssh, "df -h")
    print(f"[磁盘使用情况]\n{out2}")
    results['disk']['usage'] = out2
    
    # 检查是否有fio
    fio_check, _ = run_cmd(ssh, "which fio 2>/dev/null && echo 'found' || echo 'not found'")
    
    if 'found' in fio_check:
        print("[*] 使用 fio 进行磁盘测试...")
        
        # 顺序写入
        print("[*] 顺序写入测试 (1GB, 10秒)...")
        out3, _ = run_cmd(ssh, "fio --name=seq_write --ioengine=libaio --iodepth=32 --rw=write --bs=1M --size=1G --numjobs=1 --runtime=10 --time_based --group_reporting --output-format=terse 2>&1", timeout=60)
        print(f"[顺序写入(terse)]: {out3[:500] if out3 else 'N/A'}")
        
        # 顺序读取
        print("[*] 顺序读取测试 (1GB, 10秒)...")
        out4, _ = run_cmd(ssh, "fio --name=seq_read --ioengine=libaio --iodepth=32 --rw=read --bs=1M --size=1G --numjobs=1 --runtime=10 --time_based --group_reporting 2>&1", timeout=60)
        print(f"[顺序读取]\n{out4[-1000:] if out4 else 'N/A'}")
        results['disk']['fio_read'] = out4[-1000:] if out4 else ''
        
        # 随机4K读写
        print("[*] 随机4K IOPS测试 (10秒)...")
        out5, _ = run_cmd(ssh, "fio --name=rand_rw --ioengine=libaio --iodepth=64 --rw=randrw --bs=4K --size=512M --numjobs=4 --runtime=10 --time_based --group_reporting 2>&1", timeout=60)
        print(f"[随机4K读写]\n{out5[-1000:] if out5 else 'N/A'}")
        results['disk']['fio_rand'] = out5[-1000:] if out5 else ''
    else:
        # 备用：dd测试
        print("[*] 使用 dd 进行磁盘性能测试...")
        
        # 写入测试
        print("[*] 磁盘顺序写入测试...")
        out3, _ = run_cmd(ssh, "dd if=/dev/zero of=/tmp/testfile bs=1M count=1024 conv=fdatasync 2>&1", timeout=120)
        print(f"[磁盘写入]\n{out3}")
        results['disk']['dd_write'] = out3
        
        # 读取测试  
        print("[*] 磁盘顺序读取测试...")
        out4, _ = run_cmd(ssh, "dd if=/tmp/testfile of=/dev/null bs=1M 2>&1", timeout=60)
        print(f"[磁盘读取]\n{out4}")
        results['disk']['dd_read'] = out4
        
        # 清理
        run_cmd(ssh, "rm -f /tmp/testfile")
    
    # 磁盘IO当前状态
    out6, _ = run_cmd(ssh, "iostat -x 1 3 2>/dev/null | tail -20 || vmstat -d 2>/dev/null | head -10")
    print(f"[磁盘IO状态]\n{out6}")
    results['disk']['iostat'] = out6

def test_network(ssh):
    print("\n========== 网卡 性能测试 ==========")
    
    # 网卡信息
    out, _ = run_cmd(ssh, "ip addr show")
    print(f"[网卡信息]\n{out}")
    results['network'] = {'info': out}
    
    # 网卡详细信息
    out2, _ = run_cmd(ssh, "ip link show | grep -E 'mtu|state'")
    print(f"[网卡状态]\n{out2}")
    
    # 网卡速率
    out3, _ = run_cmd(ssh, "ethtool $(ip route | grep default | awk '{print $5}' | head -1) 2>/dev/null | grep -E 'Speed|Duplex|Auto' || cat /sys/class/net/$(ip route | grep default | awk '{print $5}' | head -1)/speed 2>/dev/null")
    print(f"[网卡速率]\n{out3 if out3 else '无法获取速率信息'}")
    results['network']['speed'] = out3
    
    # 获取默认网卡名
    iface, _ = run_cmd(ssh, "ip route | grep default | awk '{print $5}' | head -1")
    iface = iface.strip()
    
    # 网络流量统计
    if iface:
        out4, _ = run_cmd(ssh, f"cat /proc/net/dev | grep {iface}")
        print(f"[网卡流量统计]\n{out4}")
        results['network']['traffic'] = out4
    
    # iperf3带宽测试（本地回环）
    print("[*] 检查 iperf3 工具...")
    iperf_check, _ = run_cmd(ssh, "which iperf3 2>/dev/null && echo 'found' || echo 'not found'")
    
    if 'found' in iperf_check:
        print("[*] 运行 iperf3 本地回环带宽测试...")
        # 启动服务端（后台）
        run_cmd(ssh, "pkill iperf3 2>/dev/null; sleep 0.5; iperf3 -s -D -1 2>/dev/null")
        time.sleep(1)
        # 客户端测试
        out5, _ = run_cmd(ssh, "iperf3 -c 127.0.0.1 -t 5 -i 1 2>&1", timeout=30)
        print(f"[iperf3 本地回环测试]\n{out5}")
        results['network']['iperf3_loopback'] = out5
    else:
        # 备用：测试网络延迟和DNS
        print("[*] 使用基础网络测试...")
        out5, _ = run_cmd(ssh, "ping -c 5 8.8.8.8 2>&1 | tail -5")
        print(f"[外网延迟测试]\n{out5}")
        results['network']['ping_external'] = out5
        
        out6, _ = run_cmd(ssh, "ping -c 5 127.0.0.1 2>&1 | tail -5")
        print(f"[本地回环延迟]\n{out6}")
        results['network']['ping_loopback'] = out6
    
    # 网络连接状态
    out7, _ = run_cmd(ssh, "ss -s 2>/dev/null || netstat -s 2>/dev/null | head -20")
    print(f"[网络连接统计]\n{out7}")
    results['network']['connections'] = out7
    
    # 实时网速（采样2次）
    print("[*] 采样网络实时速率...")
    rate_script = "iface=" + iface + """; if [ -z "$iface" ]; then iface=$(ip route | grep default | awk '{print $5}' | head -1); fi; rx1=$(cat /proc/net/dev | grep $iface | awk '{print $2}'); tx1=$(cat /proc/net/dev | grep $iface | awk '{print $10}'); sleep 2; rx2=$(cat /proc/net/dev | grep $iface | awk '{print $2}'); tx2=$(cat /proc/net/dev | grep $iface | awk '{print $10}'); rx_rate=$(( (rx2-rx1)/2/1024 )); tx_rate=$(( (tx2-tx1)/2/1024 )); echo "Interface: $iface RX: ${rx_rate} KB/s TX: ${tx_rate} KB/s" """
    out8, _ = run_cmd(ssh, rate_script, timeout=10)
    print(f"[实时网络速率]\n{out8}")
    results['network']['realtime_rate'] = out8

def save_results():
    """保存结果到JSON文件"""
    with open(r'd:\workspace\test\benchmark_raw.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n[OK] 原始结果已保存到 benchmark_raw.json")

def main():
    print("=" * 60)
    print("  Linux 服务器性能测试")
    print(f"  目标: {HOST}")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        ssh = connect()
    except Exception as e:
        print(f"[ERROR] 连接失败: {e}")
        sys.exit(1)
    
    try:
        test_system_info(ssh)
        test_cpu(ssh)
        test_gpu(ssh)
        test_memory(ssh)
        test_disk(ssh)
        test_network(ssh)
    finally:
        save_results()
        ssh.close()
        print("\n[OK] 测试完成，连接已关闭")

if __name__ == '__main__':
    main()
