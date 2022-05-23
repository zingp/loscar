from math import log10
from pprint import pprint

MgCa_e = 4.87
MgCa_i = 3.35


def cacl_mg_ca_real(ph_diff):
    mg_ca_real = MgCa_e - 0.7 * ph_diff * MgCa_i
    return mg_ca_real


def calc_t_diff_by_mgca(mg_ca_real):
    A = 0.085
    B = 0.38
    t1 = (1/A)*log10(MgCa_i/B * (5.15/2)**0.42)
    t2 = (1/A)*log10(mg_ca_real/B * (5.15/2)**0.42)
    return t2 - t1


def calc_o18_ph(t_diff):
    O18_w = 0.5792
    O18_e = -2.01625
    O18_i = -1.1622
    O18_t = 2.32/0.09 + O18_w
    bc = (t_diff / 0.09 - 4.64*O18_i/0.09 + O18_i**2 -
          2*O18_i*O18_w + (2.32/0.09 + O18_w)**2)**0.5
    bc = float(bc)
    if bc <= 0:
        print("bc < 0 ", bc)
        return 0
    O18_t = O18_t - bc if (O18_t - bc) < 0 else O18_t + bc

    if O18_t >= 0:
        raise "calc_o18_ph error"
    return O18_e - O18_t


def cacl_cie_diff(o18_ph, t_diff):
    C13_e = 3.94
    C13_i = 0.81125
    return 4.6 - (C13_e - C13_i) + 3 * o18_ph + 0.103439 * t_diff


def verify_answer(cie1, co2_i, co2_e):
    A = 28.26
    B = 0.22
    C = 4.4*A/(23.86*B)
    cie2 = (A*B*co2_i + A*B*C)/(A+B*co2_i+B*C) - \
        (A*B*co2_e + A*B*C)/(A+B*co2_e+B*C)
    if abs(cie2 - cie1) < 0.01:
        return True, cie2 - cie1
    return False, cie2 - cie1


def final_calc(dic):
    ini_ph = round(dic["ini_ph"], 2)
    final_ph = round(dic["final_ph"], 2)
    ini_co2 = dic["ini_co2"]
    final_co2 = dic["final_co2"]
    mg_ca_real = cacl_mg_ca_real(final_ph - ini_ph)
    t_diff_mgca = calc_t_diff_by_mgca(mg_ca_real)
    # print("t_diff_mgca", t_diff_mgca)
    O18_ph = calc_o18_ph(t_diff_mgca)
    cie_diff_bymgca = cacl_cie_diff(O18_ph, t_diff_mgca)
    # print("cie_diff_bymgca:", cie_diff_bymgca)
    ok, cie_diff_final = verify_answer(-cie_diff_bymgca, ini_co2, final_co2)
    return -cie_diff_bymgca, cie_diff_final


def read_out(filename):
    """final_out, ini_co2=1200, ini_ph=7.729965675185227, final_co2=3932.49333291,
    final_ph=7.338144622526911, phdat_final_ph=7.338068536319739, dic_a=2.481350329779708,
    dic_z=3.272378669010403, alk_a=2.620073182065822, alk_z=3.248060678286949,
    finc=24832525578320.312, cinp=13696.2890625
    """
    names = ["ini_co2", "ini_ph", "final_co2", "final_ph",
             "phdat_final_ph", "dic_a", "dic_z", "alk_a", "alk_z", "finc", "cinp"]
    results = {}
    with open(filename, "r") as f:
        for line in f:
            items = line.strip().split(",")
            dic = {}
            for item in items[1:]:
                key, value = item.strip().split("=")
                value = float(value)
                # print(key, " ", value)
                dic[key] = value
            ini_ph = round(dic["ini_ph"], 2)
            if ini_ph not in results:
                results[ini_ph] = [dic]
            else:
                results[ini_ph].append(dic)
    return results


if __name__ == '__main__':
    outfile = "output.txt.total"
    r = read_out(outfile)
    # pprint(len(r.keys()))
    count = 0
    for key in sorted(r):
        # print("key", key)
        # if key == 7.68:
        #     pprint(r[key])
        for dic in r[key]:
            # print(dic["ini_co2"])
            cie_diff_bymgca, cie_diff_final = final_calc(dic=dic)
            dic["cie_diff_bymgca"] = cie_diff_bymgca
            dic["cie_diff_final"] = cie_diff_final
            for k in dic:
                dic[k] = round(dic[k], 2)
            print(dic)
            count += 1
        # print("-------")
    print("count:", count)
