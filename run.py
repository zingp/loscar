import code
import os
import sys
import time
import math
import functools
import numpy as np
import subprocess
# nohup sudo python3 -u run.py >run.log 2>&1 &

# 定义需要使用的变量
input_file = "prepetm.inp"
ph_dat = "ph.dat"
alk_file = "alk.dat"
dic_file = "dic.dat"

# 稳态final_co2允许误差
diff_co2 = 1.0

# 第一步：求稳态相关需要修改的变量
modkv = {
    "SVSTART": "",
    "TFINAL": 200e7,
    "CINP": 0.,
    "PCO2SI": 1200,
}
step1_save_fmt = "dat/out1prepetm-co2_{}.dat"

# 第二步 求ph.dat中第三列最后一行ph等于初始ph时，finc的搜索空间
mod_finc_kv = {
    "TFINAL": 200e7,
    "RESTART": "",
    "FINC": 15.83409493e12,
    "CINP": 0.,
    "PCO2SI": 0
}
max_finc = 15.83409493e13
min_finc = 12e11
step2_save_fmt = "dat/out2prepetm-co2_{}-ph_{}.dat"

# 第三步 加碳时候cinp的搜索空间
# loscar 输入文件中需要修改的值
cinp_kv = {"TFINAL": 17e3, "CINP": 0., "TCSPAN": 17e3}
min_cinp = 0
max_cinp = 30000

step3_save_fmt = "dat/out3prepetm-co2_{}-ph_{}.dat"

# ph 初始枚举值
start_ph_list = np.arange(7.80, 8.0, 0.01)

out_string = "final_out, ini_co2={}, ini_ph={}, final_co2={}, final_ph={}, phdat_final_ph={}, dic_a={}, dic_z={}, alk_a={}, alk_z={}, finc={}, cinp={}"
output_list = []
output_file = "output.txt"
max_step = 150


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        start = time.time()
        res = func(*args, **kw)
        end = time.time()
        print("duration={}s".format(round(end - start), 2))
        return res

    return wrapper


def read_final_co2(out_text):
    """读取最终CO2"""
    sep = "Final Atm CO2:"
    for line in out_text.split('\n'):
        if sep in line:
            final_co2 = float(line.split(sep)[-1].strip())
            return final_co2
    return 0.


def read_dic_alk():
    """读取dic_file, alk_file文件"""
    dicr = read_file_3thcol(dic_file)
    alkr = read_file_3thcol(alk_file)
    return dicr[0], dicr[-1], alkr[0], alkr[-1]


def get_lowest_ph_index(ini_ph, ph_list):
    for idx, v in enumerate(ph_list):
        if v >= ini_ph:
            return idx
    return -1


def write_file(dataset, file):
    with open(file, "w+", encoding="utf-8") as f:
        for line in dataset:
            f.write(line + "\n")
    print("write to {}".format(file))


def calc_final_ph(pHp):
    """公式法通过初始ph计算最终ph"""
    alpha1 = 1.0191
    alpha2 = 1.0189
    epsilon1 = 19.12
    epsilon2 = 18.88
    d11Bsw = 39.61
    d11Bp = 15.35
    d11Be = 14.79
    # d11Be = 14.50
    pKB1 = 8.526
    pKB2 = 8.461
    m = (1 + 10**(pKB1 - pHp)) / (1 + alpha1 * 10**(pKB1 - pHp))
    b = (-d11Bp - 10**(pKB1 - pHp) *
         (epsilon1 + alpha1 * d11Bp)) / (1 + 10**(pKB1 - pHp))
    pHe = pKB2 - math.log10(-(d11Bsw - d11Be - (m * d11Bsw + b)) /
                            (d11Bsw - alpha2 *
                             (d11Be + m * d11Bsw + b) - epsilon2))
    return pHe


def mod_file(file, modkv={}):
    """修改输入文件中的变量值"""
    file2 = file + ".copy"
    res = os.popen("mv {} {}".format(file, file2))
    print(res.read())
    tmp_str = ""
    mod_str = ""
    with open(file2, "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#"):
                for k, v in modkv.items():
                    if k in line:
                        line = "{}   {}\n".format(k, v)
                        mod_str += "  {}  {}".format(k, v)
            tmp_str += line
    with open(file, "w", encoding="utf-8") as f:
        f.write(tmp_str)
        f.flush()
    print(mod_str)


def read_file_3thcol(file):
    """读取输出文件第三列"""
    third_cols = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            li = line.split()
            if len(li) < 3:
                raise "ERROR"
            x = float(li[2])
            third_cols.append(x)
    return third_cols


# def read_file(file):
#     print("read_file", file)
#     with open(file, "r", encoding="utf-8") as f:
#         for line in f:
#             if line.startswith("#"):
#                 continue
#             if "PCO2SI" in line:
#                 print(line)


def calc_stable(ini_co2):
    """step1: 求稳态"""
    # 重置初始输入文件
    r = os.popen("cp prepetm.inp.2 prepetm.inp")
    _ = r.read()

    # 修改输入文件中的变量值
    modkv["PCO2SI"] = ini_co2
    modkv["SVSTART"] = step1_save_fmt.format(ini_co2)
    mod_file(input_file, modkv)
    #     read_file(input_file)
    # 运行loscar
    loscar_res = os.popen("./loscar.x prepetm.inp")
    res_text = loscar_res.read()
    final_co2 = read_final_co2(res_text)
    print("ini_co2={}, final_co2={}".format(ini_co2, final_co2))
    if abs(ini_co2 - final_co2) > 0.01:
        print("ini_co2={}, final_co2={} *".format(ini_co2, final_co2))
        return -1
    return 0


def binary_search_finc(input_file, min_finc, max_finc, ini_ph, mod_finc_kv):
    """step2: 二分搜索finc, 使ph.dat 中最后一行ph等于输入的ini_ph"""
    info = "2_finc, ini_co2={}, finc={}, dat_last_ph={}, ini_ph={}, final_co2={} {}"
    mod_finc_kv["RESTART"] = modkv["SVSTART"]
    mod_finc_kv["PCO2SI"] = modkv["PCO2SI"]
    mod_finc_kv["SVSTART"] = step2_save_fmt.format(
        modkv["PCO2SI"], round(ini_ph, 2))
    step = 0
    last_ph_tmp = float('inf')
    while max_finc - min_finc > 1e-4:
        step += 1
        # print("2_search_finc, step:", step)
        finc = (max_finc + min_finc) / 2
        mod_finc_kv["FINC"] = finc
        mod_file(input_file, mod_finc_kv)
        res = os.popen("./loscar.x prepetm.inp")
        cmd_text = res.read()
        ph_list = read_file_3thcol(ph_dat)
        last_ph = ph_list[-1]
        if last_ph - ini_ph >= 1e-4:
            max_finc = finc
        elif last_ph - ini_ph <= -1e-4:
            min_finc = finc
        else:
            final_co2 = read_final_co2(cmd_text)
            tag = ''
            if abs(final_co2 - modkv["PCO2SI"]) >= diff_co2:
                tag = '*'
                print(info.format(modkv["PCO2SI"], finc,
                      last_ph, ini_ph, final_co2, tag))
                return -1
            print(info.format(modkv["PCO2SI"], finc,
                  last_ph, ini_ph, final_co2, tag))
            return 0
        if step % 5 == 0:
            print("2_finc, step={}, ph_list0={}, cur_end_ph={}, ini_ph={}"
                  .format(step, ph_list[0], last_ph, ini_ph))
        if abs(last_ph_tmp - last_ph) < 1e-4:
            break
        if step >= max_step:
            break
        last_ph_tmp = last_ph
    else:
        print("2_finc failed, finc={}, dat_last_ph={}, ini_ph={}".format(
            finc, last_ph, ini_ph))
        write_file(output_list, output_file)
    return -1


def binary_search_cinp(input_file, min_cinp, max_cinp, ini_ph, end_ph,
                       cinp_kv):
    """step3:加碳, 二分查找搜索cinp 使得end_ph等于给定值"""
    info = "msg={}, step={}, ph_list_ini={}, cur_end_ph={}, end_ph={}"
    # cinp的值也应该记录一下
    cinp_kv["RESTART"] = mod_finc_kv["SVSTART"]
    cinp_kv["PCO2SI"] = modkv["PCO2SI"]
    cinp_kv["FINC"] = mod_finc_kv["FINC"]
    cinp_kv["SVSTART"] = step3_save_fmt.format(modkv["PCO2SI"],
                                               round(ini_ph, 2))
    step = 0
    last_ph = float('inf')
    ph_list = []
    while max_cinp - min_cinp > 1e-4:
        step += 1
        cinp = (max_cinp + min_cinp) / 2
        cinp_kv["CINP"] = cinp
        mod_file(input_file, cinp_kv)
        loscar_out = os.popen("./loscar.x prepetm.inp")
        loscar_out_text = loscar_out.read()
        ph_list = read_file_3thcol(ph_dat)
        cur_end_ph = ph_list[-1]
        if abs(cur_end_ph - end_ph) <= 1e-4:
            # 说明找到了
            start_co2 = modkv["PCO2SI"]
            final_co2 = read_final_co2(loscar_out_text)
            x, y, m, n = read_dic_alk()
            out = out_string.format(start_co2, ph_list[0], final_co2, end_ph,
                                    cur_end_ph, x, y, m, n,
                                    mod_finc_kv["FINC"], cinp)
            output_list.append(out)
            print(out)
            return
        if cur_end_ph - end_ph > 1e-4:
            min_cinp = cinp
        elif cur_end_ph - end_ph < -1e-4:
            max_cinp = cinp
        if step % 1 == 0:
            msg = "3_cinp ok"
            print(info.format(msg, step, ph_list[0], cur_end_ph, end_ph))
        if abs(last_ph - cur_end_ph) < 1e-4:
            msg = "3_cinp ph converging"
            print(info.format(msg, step, ph_list[0], cur_end_ph, end_ph))
            return
        if step >= max_step:
            return
        last_ph = cur_end_ph
    if ph_list:
        msg = "3_cinp wihle end"
        print(info.format(msg, step, ph_list[0], ph_list[-1], end_ph))
    write_file(output_list, output_file)


def binary_search_extremum_ph(input_file,
                              min_finc,
                              max_finc,
                              ini_ph,
                              mod_finc_kv,
                              ismax=False):
    """搜索初始ph的上下界"""
    mod_finc_kv["RESTART"] = modkv["SVSTART"]
    mod_finc_kv["PCO2SI"] = modkv["PCO2SI"]
    mod_finc_kv["SVSTART"] = step2_save_fmt.format(modkv["PCO2SI"],
                                                   round(ini_ph, 2))
    step = 0
    last_calc_ini_ph = float('inf')
    while max_finc - min_finc > 1e-4:
        step += 1
        # print("binary_search_finc, step:", step)
        finc = (max_finc + min_finc) / 2
        mod_finc_kv["FINC"] = finc
        mod_file(input_file, mod_finc_kv)
        res = os.popen("./loscar.x prepetm.inp")
        _ = res.read()
        ph_list = read_file_3thcol(ph_dat)
        cur_ph = ph_list[-1]
        if (ismax and cur_ph >= ini_ph) or ((not ismax) and cur_ph <= ini_ph):
            return ini_ph
        if cur_ph - ini_ph >= 1e-4:
            max_finc = finc
        elif cur_ph - ini_ph <= -1e-4:
            min_finc = finc
        else:
            return ini_ph
        if abs(last_calc_ini_ph - cur_ph) < 1e-4:
            return cur_ph
        if step >= max_step:
            break
        last_calc_ini_ph = cur_ph
    return -1


def run_cmd(cmd):
    """
    这段代码执行一个指定的命令并将执行结果以一个字节字符串的形式返回。 如果你需要文本形式返回，加一个解码步骤即可。例如：
        out_text = out_bytes.decode('utf-8')
    如果被执行的命令以非零码返回，就会抛出异常。 
    默认情况下,check_output() 仅仅返回输入到标准输出的值。 如果需要同时收集标准输出和错误输出，使用 stderr 参数：
    """
    try:
        out_bytes = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT)
        code = 0
    except subprocess.CalledProcessError as e:
        out_bytes = e.output
        code = e.returncode
    return [code, out_bytes.decode(encoding='utf-8')]


if __name__ == "__main__":
    r = os.popen("cp prepetm.inp prepetm.inp.2")
    _ = r.read()
    # 公式法求对应的final ph的值
    end_ph_list = [
        calc_final_ph(round(start_ph_list[i], 4))
        for i in range(start_ph_list.size)
    ]

    # 二氧化碳枚举值
    ini_co2_list = list(range(1000, 1201, 20))

    for i in range(len(ini_co2_list)):
        print("***---1.求稳态CO2={}---***".format(ini_co2_list[i]))
        r = calc_stable(ini_co2_list[i])
        if r < 0:
            print("没有求到稳态！")
            continue
        min_ph_cap = binary_search_extremum_ph(input_file, min_finc, max_finc,
                                               start_ph_list[0], mod_finc_kv)
        min_idx = get_lowest_ph_index(min_ph_cap, start_ph_list)
        max_ph_cap = binary_search_extremum_ph(input_file,
                                               min_finc,
                                               max_finc,
                                               start_ph_list[-1],
                                               mod_finc_kv,
                                               ismax=True)
        max_idx = get_lowest_ph_index(max_ph_cap, start_ph_list)
        print("co2={}, min_ph_cap={}, idx1={}, max_ph_cap={}, idx2={}".format(
            ini_co2_list[i], min_ph_cap, min_idx, max_ph_cap, max_idx))
        if min_idx < 0 or min_idx > len(start_ph_list) or max_idx > len(start_ph_list) or max_idx < 0:
            continue
        for j in range(min_idx, max_idx):
            start = time.time()
            print("***---2.求初始PH={}---***".format(start_ph_list[j]))
            code = binary_search_finc(input_file, min_finc, max_finc,
                                      start_ph_list[j], mod_finc_kv)
            if code < 0:
                continue
            print("***---3.加碳---***")
            binary_search_cinp(input_file, min_cinp, max_cinp,
                               start_ph_list[j], end_ph_list[j], cinp_kv)
            end = time.time()
            write_file(output_list, output_file)
            print("duration={}s".format(round(end - start), 2))
            print("#" * 50)
