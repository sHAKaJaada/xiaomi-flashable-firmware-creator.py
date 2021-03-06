from argparse import ArgumentParser
from datetime import datetime
from distutils.dir_util import copy_tree
from os import makedirs, rename, remove, path
from shutil import move, make_archive, rmtree
from socket import gethostname
from sys import exit
from zipfile import ZipFile


def arg_parse():
    process = "None"
    rom = "None"
    switches = ArgumentParser(description='Xiaomi Flashable Firmware Creator', )
    group = switches.add_mutually_exclusive_group(required=True)
    group.add_argument("-F", "--firmware", help="Create normal Firmware zip")
    group.add_argument("-N", "--nonarb", help="Create non-ARB Firmware zip")
    group.add_argument("-L", "--firmwareless", help="Create Firmware-less zip")
    group.add_argument("-V", "--vendor", help="Create Firmware+Vendor zip")
    args = vars(switches.parse_args())
    firmware = args["firmware"]
    firmwareless = args["firmwareless"]
    nonarb = args["nonarb"]
    vendor = args["vendor"]
    if firmware is not None:
        process = "firmware"
        rom = firmware
    elif nonarb is not None:
        process = "nonarb"
        rom = nonarb
    elif firmwareless is not None:
        process = "firmwareless"
        rom = firmwareless
    elif vendor is not None:
        process = "vendor"
        rom = vendor
    return rom, process


def pre():
    today = str(datetime.today()).split('.')[0]
    host = str(gethostname())
    return today, host


def check_firmware():
    if path.exists('tmp/firmware-update') \
            or path.exists('tmp/META-INF/com/google/android/update-binary') \
            or path.exists('tmp/META-INF/com/google/android/updater-script'):
        pass
    else:
        print("This zip doesn't contain firmware directory.")
        rmtree("tmp")
        exit(1)


def firmware_extract():
    rom, process = arg_parse()
    if process == "firmware":
        with ZipFile(rom, 'r') as z:
            files = [n for n in z.namelist()
                     if n.startswith('firmware-update/') or n.startswith('META-INF/')]
            z.extractall(path="tmp", members=files)
    elif process == "nonarb":
        with ZipFile(rom, 'r') as z:
            files = [n for n in z.namelist()
                     if n.startswith('firmware-update/dspso.bin')
                     or n.startswith('firmware-update/BTFM.bin')
                     or n.startswith('firmware-update/NON-HLOS.bin')
                     or n.startswith('META-INF/')]
            z.extractall(path="tmp", members=files)
    check_firmware()
    move('tmp/firmware-update/', 'out/firmware-update/')
    move("tmp" + '/META-INF/com/google/android/update-binary', 'out/META-INF/com/google/android/')


def rom_extract():
    rom, process = arg_parse()
    with ZipFile(rom, 'r') as z:
        files = [n for n in z.namelist()
                 if not n.startswith('firmware-update/')]
        z.extractall(path="tmp", members=files)
    check_firmware()
    copy_tree('tmp/', 'out/')


def vendor_extract():
    rom, process = arg_parse()
    with ZipFile(rom, 'r') as z:
        files = [n for n in z.namelist()
                 if not n.startswith('system') and not n.startswith('boot')]
        z.extractall(path="tmp", members=files)
    check_firmware()
    copy_tree('tmp/', 'out/')
    remove("out/META-INF/com/google/android/updater-script")


def firmware_updater():
    today, host = pre()
    with open("tmp/META-INF/com/google/android/updater-script", 'r') as i, \
            open("out/updater-script", "w", newline='\n') as o:
        o.writelines("show_progress(0.200000, 10);" + '\n' + '\n')
        o.writelines("# Generated by Xiaomi Flashable Firmware Creator" + '\n'
                     + "# " + today + " - " + host + '\n' + '\n')
        o.writelines('ui_print("Flashing Normal firmware...");' + '\n')
        o.writelines(line for line in i if "getprop" in line or "Target" in line or "firmware-update" in line)
        o.writelines('\n' + "show_progress(0.100000, 2);" + '\n' + "set_progress(1.000000);" + '\n')
    with open("out/updater-script", 'r') as i, \
            open("out/META-INF/com/google/android/updater-script", "w", newline='\n') as o:
        correct = i.read().replace('/firmware/image/sec.dat', '/dev/block/bootdevice/by-name/sec')\
            .replace('/firmware/image/splash.img', '/dev/block/bootdevice/by-name/splash')
        o.write(correct)
    remove("out/updater-script")


def nonarb_updater():
    today, host = pre()
    with open("tmp/META-INF/com/google/android/updater-script", 'r') as i, \
            open("out/updater-script", "w", newline='\n') as o:
        o.writelines("show_progress(0.200000, 10);" + '\n' + '\n')
        o.writelines("# Generated by Xiaomi Flashable Firmware Creator" + '\n'
                     + "# " + today + " - " + host + '\n' + '\n')
        o.writelines('ui_print("Flashing non-ARB firmware...");' + '\n')
        o.writelines(line for line in i if "getprop" in line or "Target" in line
                     or "modem" in line or "bluetooth" in line or "dsp" in line)
        o.writelines('\n' + "show_progress(0.100000, 2);" + '\n' + "set_progress(1.000000);" + '\n')
    with open("out/updater-script", 'r') as i, \
            open("out/META-INF/com/google/android/updater-script", "w", newline='\n') as o:
        correct = i.read().replace('/firmware/image/sec.dat', '/dev/block/bootdevice/by-name/sec')\
            .replace('/firmware/image/splash.img', '/dev/block/bootdevice/by-name/splash')
        o.write(correct)
    remove("out/updater-script")


def firmwareless_updater():
    today, host = pre()
    with open("tmp/META-INF/com/google/android/updater-script", 'r') as i, \
            open("out/META-INF/com/google/android/updater-script", "w", newline='\n') as o:
        o.writelines("show_progress(0.200000, 10);" + '\n' + '\n')
        o.writelines("# Generated by Xiaomi Flashable Firmware Creator" + '\n'
                     + "# " + today + " - " + host + '\n' + '\n')
        o.writelines('ui_print("Flashing firmware-less ROM...");' + '\n')
        o.writelines(line for line in i if "getprop" in line or "Target" in line
                     or "boot.img" in line or "system" in line or "vendor" in line)
        o.writelines('\n' + "show_progress(0.100000, 2);" + '\n' + "set_progress(1.000000);" + '\n')


def vendor_updater():
    today, host = pre()
    with open("tmp/META-INF/com/google/android/updater-script", 'r') as i, \
            open("out/updater-script", "w", newline='\n') as o:
        o.writelines("show_progress(0.200000, 10);" + '\n' + '\n')
        o.writelines("# Generated by Xiaomi Flashable Firmware Creator" + '\n'
                     + "# " + today + " - " + host + '\n' + '\n')
        o.writelines('ui_print("Flashing firmware + vendor...");' + '\n')
        o.writelines(line for line in i if "getprop" in line or "Target" in line or "firmware-update" in line
                     or "vendor" in line)
        o.writelines('\n' + "show_progress(0.100000, 2);" + '\n' + "set_progress(1.000000);" + '\n')
    with open("out/updater-script", 'r') as i, \
            open("out/META-INF/com/google/android/updater-script", "w", newline='\n') as o:
        correct = i.read().replace('/firmware/image/sec.dat', '/dev/block/bootdevice/by-name/sec')\
            .replace('/firmware/image/splash.img', '/dev/block/bootdevice/by-name/splash')
        o.write(correct)
    remove("out/updater-script")


def make_zip():
    rom, process = arg_parse()
    with open("out/META-INF/com/google/android/updater-script", 'r') as i:
        codename = str(i.readlines()[7].split('/', 3)[2]).split(':', 1)[0].replace('_', '-')
    print("Creating " + process + " zip from " + rom + " for " + codename)
    make_archive('firmware', 'zip', 'out/')
    if path.exists('firmware.zip'):
        if process == "firmware":
            rename('firmware.zip', 'fw_' + codename + "_" + rom)
        elif process == "nonarb":
            rename('firmware.zip', 'fw-non-arb_' + codename + "_" + rom)
        elif process == "firmwareless":
            rename('firmware.zip', 'fw-less_' + codename + "_" + rom)
        elif process == "vendor":
            rename('firmware.zip', 'fw-vendor_' + codename + "_" + rom)
        print("All done!")
        rmtree("tmp")
        rmtree('out')
    else:
        print("Failed!" + '\n' + "Check out folder!")


def main():
    rom, process = arg_parse()
    makedirs("tmp", exist_ok=True)
    makedirs("out", exist_ok=True)
    makedirs("out/META-INF/com/google/android", exist_ok=True)
    if process == "firmware":
        print("Unzipping MIUI..")
        firmware_extract()
        print("Generating updater-script..")
        firmware_updater()
    elif process == "nonarb":
        print("Unzipping MIUI..")
        firmware_extract()
        print("Generating updater-script..")
        nonarb_updater()
    elif process == "firmwareless":
        print("Unzipping MIUI..")
        rom_extract()
        print("Generating updater-script..")
        firmwareless_updater()
    elif process == "vendor":
        print("Unzipping MIUI..")
        vendor_extract()
        print("Generating updater-script..")
        vendor_updater()
    make_zip()


arg_parse()
main()
