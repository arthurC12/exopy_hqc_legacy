import ADwin
import os.path
import time
out_voltage = 0.015
out_bin = int((out_voltage+10)*2**16/20)
print(out_bin)
adw = ADwin.ADwin(1, 1)
boot_script = r'C:\ADwin\ADwin11.btl'
adw.Boot(boot_script)
lib_dir = ''
adw.Load_Process(os.path.join(lib_dir, 'setvoltage.TB1'))
adw.Load_Process(os.path.join(lib_dir, 'getvoltage.TB1'))
adw.Set_Par(1, out_bin)
adw.Set_Par(2, 1)
adw.Set_Par(3, 1)
adw.Set_Par(5, 1)
adw.Set_Par(6, 1)
adw.Start_Process(1)
check = True
while check:
    p5 = adw.Get_Par(5)
    if p5 == 1:
        time.sleep(1.0/25)
    else:
        adw.Stop_Process(1)
        check = False

adw.Start_Process(2)
check = True
while check:
    p6 = adw.Get_Par(6)
    if p6 == 1:
        time.sleep(1.0/25)
    else:
        adw.Stop_Process(2)
        check = False
in_bin = adw.Get_Par(4) >> 6
in_voltage = 20*in_bin/2**18 - 10
print(in_voltage)