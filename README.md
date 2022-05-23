# loscar
## 介绍
- run.py 用于求解ini_ph, final_ph, ini_co2, final_co2等
- run_final 计算delta cie

## 运行环境
- Linux
- python3.8+

## 运行方式 
### run.py
- 将所有文件放在LOSCAR程序根目录下，原LOSCAR程序必须先编译好，编译命令`make loscar PALEO=1`
- 自定义枚举区间(如有必要), 修改初始ph的枚举区间`start_ph_list` , 默认是[7.80, 8.0]; 修改初始co2的枚举区间`ini_co2_list` 默认是[1000, 1201)
- 运行`nohup sudo python3 -u run.py >run.log 2>&1 &`， 其中输出结果在`output.txt`, 程序打印日志`run.log`

### run_final.py
- 修改run_final.py98行`outfile = "output.txt.total"`中的输入文件为run.py的output文件，然后运行`python3 run_final.py`


## TODO
- debug中