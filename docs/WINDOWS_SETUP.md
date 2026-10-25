# Windows Setup Guide: from a clean laptop to a running WLAN AttackLab demo

This guide assumes **no prior experience** with virtual machines, Linux,
or the terminal. Follow the steps in order. Every command block is
labeled with **where to run it**:

- 🪟 **Windows PowerShell** — open via Start Menu → type `PowerShell` → Enter
- 🐧 **Kali terminal** — a terminal window inside the Kali Linux VM, opened after step 4
- 🎯 **Vulnerable target console** — only needed once, for its own IP check

Never mix 🪟 and 🐧 commands — they use different syntax.

---

## 1. Check CPU virtualization is enabled

🪟 PowerShell (as Administrator — right-click PowerShell → "Run as administrator"):

```powershell
systeminfo
```

Scroll to **"Hyper-V Requirements"**. You want to see:

```
Virtualization Enabled In Firmware: Yes
```

If it says **No**, go to step 2. If **Yes**, skip to step 3.

## 2. Enable virtualization if disabled

This is a BIOS/UEFI setting, not a Windows setting, so steps vary by
laptop manufacturer:

1. Restart your laptop.
2. While it boots, press the key for your BIOS/UEFI setup (commonly
   `F2`, `F10`, `Del`, or `Esc` — your boot screen usually shows it).
3. Find a setting called **"Intel VT-x"**, **"AMD-V"**, **"SVM Mode"**,
   or **"Virtualization Technology"** and set it to **Enabled**.
4. Save and exit (commonly `F10`).
5. Re-run the `systeminfo` check from step 1 to confirm.

**Common error:** If you also have "Hyper-V" or "Windows Hypervisor
Platform" enabled as a Windows feature, VirtualBox can conflict with
it. If VirtualBox VMs fail to start later with a "VT-x is not
available" error, open **"Turn Windows features on or off"** and
un-check **Hyper-V**, **Virtual Machine Platform**, and **Windows
Hypervisor Platform**, then restart.

## 3. Install VirtualBox

- **What it is:** a free hypervisor that runs Linux VMs on your Windows laptop.
- **Why:** Kali and the vulnerable target both run inside VirtualBox, isolated from your host network.
- **Official download:** https://www.virtualbox.org/wiki/Downloads — download the Windows host installer.
- **Verify the current recommended version and release notes** on that page before installing (versions change).

🪟 Steps:
1. Run the downloaded `VirtualBox-x.x.x-Win.exe` installer, keep defaults, let it install (it will briefly disconnect your network adapters — this is normal).
2. Verify install:

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" --version
```

You should see a version string printed, e.g. `7.0.x`.

**Common error:** "VirtualBox cannot access the kernel driver" on
Windows 11 usually means Hyper-V/VMP is still on — see step 2's note.

## 4. Download and import Kali Linux

- **What it is:** the Linux distribution that runs the app and its security tools.
- **Official source:** https://www.kali.org/get-kali/#kali-virtual-machines — choose the **VirtualBox** pre-built image (`.7z` with a `.vbox`/`.ova`).
- **Verify the checksum** Kali publishes on that page against your download (right-click file → checksum tool, or `Get-FileHash` in PowerShell) before importing.

🪟 Steps:
1. Extract the downloaded archive (7-Zip: https://www.7-zip.org/).
2. Open VirtualBox Manager → **File → Import Appliance** → select the extracted `.ova`/`.vbox` file → **Next** → **Import**.
3. Wait for import to finish (several minutes).

## 5. Download and import the vulnerable target VM

For the Metasploit module, this project is designed around
**Metasploitable2**, a deliberately vulnerable Linux VM published for
security training.

- **Official/reputable source:** the Rapid7 / SourceForge Metasploitable2 page (search "Metasploitable2 download Rapid7" and use the official Rapid7-linked SourceForge listing). **Verify the page is legitimate and check any published checksum before importing.**
- This project does **not** bundle this image — you must obtain it yourself, per its own license/terms.

🪟 Steps:
1. Extract the downloaded `.zip` to get the `.vmdk` disk file.
2. VirtualBox Manager → **Machine → New** → name it `Metasploitable2`, type Linux, version "Other Linux (64-bit)" (or 32-bit, check the image).
3. When asked for a hard disk, choose **"Use an existing virtual hard disk file"** and select the extracted `.vmdk`.
4. Finish the wizard.

## 6. Assign RAM, CPU, and disk

With 32 GB RAM total on your laptop, a reasonable split:

| VM | RAM | CPUs |
|---|---|---|
| Kali | 8 GB | 2 |
| Metasploitable2 | 2 GB | 1 |
| (leave for Windows) | remaining ~22 GB | — |

🪟 In VirtualBox Manager, select each VM → **Settings → System** → set
**Base Memory** and **Processor** per the table. Disk size is fixed by
the imported image; no change needed.

## 7. Configure NAT and host-only adapters correctly

This is the most important networking step — it keeps the vulnerable
VM isolated.

🪟 First, create a host-only network:
1. VirtualBox Manager → **Tools → Network** (or **File → Host Network Manager** in older versions).
2. Click **Create**. Note the network it creates, e.g. `VirtualBox Host-Only Ethernet Adapter` with a DHCP range like `192.168.56.0/24`.

🪟 Configure Kali (select Kali VM → **Settings → Network**):
- **Adapter 1:** Attached to: **NAT** (for internet access to install packages).
- **Adapter 2:** Attached to: **Host-only Adapter**, select the adapter created above. Enable this adapter (checkbox).

🪟 Configure Metasploitable2 (select it → **Settings → Network**):
- **Adapter 1:** Attached to: **Host-only Adapter**, same adapter as Kali's Adapter 2.
- Make sure **no other adapter is enabled** for this VM — specifically, **do not** attach a Bridged or NAT adapter to it. It should only ever be reachable from Kali's host-only network.

Do **not** enable IP forwarding or NAT on Kali for the vulnerable
target — it should stay unreachable from anywhere except Kali itself.

## 8. Identifying actual IP addresses

Addresses vary per machine — never hardcode an IP you haven't
confirmed.

🐧 In the Kali terminal, after logging in (default Kali credentials are
on the download page — change them):

```bash
ip addr show
```

Look for the interface on the `192.168.56.x` range (or whatever your
host-only network uses) — that's Kali's host-only IP. Note it.

🎯 In the Metasploitable2 console (default login `msfadmin` / `msfadmin`
— you'll want to change this too):

```bash
ifconfig
```

Note its `192.168.56.x` address — this is the value you'll put in
`LAB_TARGET_HOST` in the backend `.env` file (step 14).

## 9. Getting the project files into Kali

If you downloaded this project as a folder/zip on Windows, the
simplest path is a **shared folder**:

🪟 Kali VM → **Settings → Shared Folders → Add** → point it at the
folder containing `wlan-attacklab` on Windows, check **Auto-mount**.

🐧 Inside Kali, after the VM boots with Guest Additions installed (Kali
images usually include them; if the shared folder doesn't appear,
install `virtualbox-guest-utils` and reboot):

```bash
cp -r /media/sf_<your-shared-folder-name>/wlan-attacklab ~/wlan-attacklab
cd ~/wlan-attacklab
```

## 10. Installing application dependencies inside Kali

🐧:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nodejs npm aircrack-ng wireshark-common tshark metasploit-framework
```

When `tshark` asks "Should non-superusers be able to capture packets?"
choose **Yes** if you plan to inspect your own captures as a normal
user; this project only ever reads already-saved files, so either
answer is fine.

**Verification:**

```bash
aircrack-ng --help | head -1
tshark --version | head -1
capinfos --version
msfconsole --version
node --version
python3 --version
```

Each should print a version line. **Common error:** `apt` fails with
"Unable to fetch" — check Kali's NAT adapter (Adapter 1) is attached
and the VM has internet via `ping -c 2 8.8.8.8`.

## 11. Preparing the Python virtual environment

🐧:

```bash
cd ~/wlan-attacklab/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Verification:** `pip list` should show `fastapi`, `sqlalchemy`,
`reportlab`, etc.

## 12. Installing frontend packages

🐧:

```bash
cd ~/wlan-attacklab/frontend
npm install
```

**Verification:** `npm run typecheck` should finish with no errors.

## 13. Installing or verifying required lab tools

Already covered in step 10 (`aircrack-ng`, `tshark`, `capinfos`,
`metasploit-framework`). If any are missing, the app's **Environment
Doctor** page will say so and the app will fall back to demonstration
mode for that specific feature — it won't crash.

## 14. Creating the environment file

🐧:

```bash
cd ~/wlan-attacklab/backend
cp .env.example .env
nano .env
```

Set at minimum:

```
EXECUTION_MODE=real
LAB_TARGET_HOST=192.168.56.x   # the Metasploitable2 IP from step 8
LAB_TARGET_ALLOWED_CIDR=192.168.56.0/24   # match your actual host-only subnet
```

Save with `Ctrl+O`, Enter, then `Ctrl+X` to exit nano.

If Windows will access the app's browser UI while the backend runs
**inside** Kali (recommended, simplest setup), also set:

```
BIND_HOST=0.0.0.0
CORS_ALLOW_ORIGINS=http://<kali-host-only-ip>:5173
```

and consider setting `REQUIRE_ACCESS_TOKEN=true` with an `ACCESS_TOKEN`
value, since the backend is then reachable beyond loopback.

## 15. Initializing the database

🐧 (the database initializes automatically on first run, but you can
pre-create it):

```bash
cd ~/wlan-attacklab/backend
source .venv/bin/activate
python3 -c "from app.core.database import init_db; init_db()"
```

**Verification:** a `data/attacklab.db` file should now exist.

## 16. Running environment checks

Start the backend (next step) then open the **Environment Doctor** page
in the browser — it runs all checks for you. You can also check from
the terminal:

```bash
curl http://127.0.0.1:8000/api/doctor
```

## 17. Starting the backend and frontend

🐧 Terminal 1:

```bash
cd ~/wlan-attacklab/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

🐧 Terminal 2:

```bash
cd ~/wlan-attacklab/frontend
echo "VITE_API_BASE_URL=http://<kali-host-only-ip>:8000" > .env
npm run dev -- --host 0.0.0.0
```

(Or use `scripts/start-dev.sh` to do both — see section 11 of the README.)

## 18. Opening the correct URL in the Windows browser

🪟 In a Windows browser, go to:

```
http://<kali-host-only-ip>:5173
```

using the IP you noted in step 8 for Kali (not `localhost` — that
refers to Windows itself, not the VM).

## 19. Running the three experiments

See `docs/DEMO_GUIDE.md` for a presentation-ready walkthrough of all
three modules.

## 20. Exporting a report

From any completed session's detail view, click **"Download PDF
report"** or **"Download JSON"**.

## 21. Stopping the app and shutting down the lab safely

🐧 In each terminal running the app: `Ctrl+C`.

🪟 In VirtualBox Manager, right-click each running VM → **Close → Send
the shutdown signal** (graceful), or shut down from inside each VM
with `sudo poweroff`.
