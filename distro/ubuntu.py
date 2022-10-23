from functions import *


def config(de_name: str, distro_version: str, username: str, root_partuuid: str, verbose: bool) -> None:
    set_verbose(verbose)
    print_status("Configuring Ubuntu")

    # add missing apt sources
    with open("/etc/apt/sources.list", "a") as file:
        file.write(
            f"\ndeb http://archive.ubuntu.com/ubuntu {distro_version}-backports main restricted universe multiverse\n")
        file.write(
            f"\ndeb http://security.ubuntu.com/ubuntu {distro_version}-security main restricted universe multiverse\n")
        file.write(
            f"\ndeb http://archive.ubuntu.com/ubuntu {distro_version}-updates main restricted universe multiverse\n")

    print_status("Installing dependencies")
    chroot("apt-get update -y")
    chroot("apt-get install -y linux-firmware network-manager software-properties-common")
    chroot("apt-get install -y git cgpt vboot-kernel-utils cloud-utils rsync")  # postinstall dependencies

    print_status("Downloading and installing de, might take a while")
    start_progress()  # start fake progress
    match de_name:
        case "gnome":
            print_status("Installing GNOME")
            chroot("apt-get install -y ubuntu-desktop gnome-software epiphany-browser")
        case "kde":
            print_status("Installing KDE")
            chroot("apt-get install -y kde-standard")
        case "xfce":
            print_status("Installing Xfce")
            chroot("apt-get install -y --no-install-recommends xubuntu-desktop gnome-software epiphany-browser")
            chroot("apt-get install -y xfce4-goodies")
        case "lxqt":
            print_status("Installing LXQt")
            chroot("apt-get install -y lubuntu-desktop discover konqueror")
        case "deepin":
            print_status("Installing deepin")
            print_error("Deepin is currently broken on Ubuntu, please select another DE")
            exit(1)

            # Probably due to some misconfiguration in deepin's installer, our kernel version is not supported.
            # Install fails with: Errors were encountered while processing: deepin-anything-dkms, dde-file-manager,
            # ubuntudde-dde, deepin-anything-server

            # TODO: Fix deepin
            chroot("add-apt-repository -y ppa:ubuntudde-dev/stable")
            chroot("apt-get update -y")
            chroot("apt-get install -y ubuntudde-dde")
        case "budgie":
            print_status("Installing Budgie")
            # do not install tex-common, it breaks the installation
            chroot("DEBIAN_FRONTEND=noninteractive apt-get install -y ubuntu-budgie-desktop tex-common-")
            chroot("dpkg-reconfigure lightdm")
        case "cli":
            print_status("Skipping desktop environment install")
        case _:
            print_error("Invalid desktop environment! Please create an issue")
            exit(1)
    stop_progress()  # stop fake progress

    # GDM3 auto installs gnome-minimal. Gotta remove it if user didn't choose gnome
    if not de_name == "gnome":
        rmfile("/mnt/depthboot/usr/share/xsessions/ubuntu.desktop")
        chroot("apt-get remove -y gnome-shell")
        chroot("apt-get autoremove -y")

    # Fix gdm3, https://askubuntu.com/questions/1239503/ubuntu-20-04-and-20-10-etc-securetty-no-such-file-or-directory
    try:
        cpfile("/mnt/depthboot/usr/share/doc/util-linux/examples/securetty", "/mnt/depthboot/etc/securetty")
    except FileNotFoundError:
        pass
    print_status("Desktop environment setup complete")

    # Replace input-synaptics with newer input-libinput, for better touchpad support
    print_status("Upgrading touchpad drivers")
    chroot("apt-get remove -y xserver-xorg-input-synaptics")
    # chroot("apt-get install -y xserver-xorg-input-libinput")

    # Add depthboot to version(this is purely cosmetic)
    with open("/mnt/depthboot/etc/os-release", "r") as f:
        os_release = f.readlines()
    os_release[1] = os_release[1][:-2] + ' (Depthboot)"\n'
    os_release[4] = os_release[4][:-2] + ' (Depthboot)"\n'
    with open("/mnt/depthboot/etc/os-release", "w") as f:
        f.writelines(os_release)

    print_status("Ubuntu setup complete")


def chroot(command: str) -> None:
    if verbose:
        bash(f'chroot /mnt/depthboot /bin/bash -c "{command}"')
    else:
        bash(f'chroot /mnt/depthboot /bin/bash -c "{command}" 2>/dev/null 1>/dev/null')  # supress all output
