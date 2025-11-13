# Raspberry Pi - Day 1 Unboxing Checklist

Just the basics to get your Pi up and running. We'll worry about FlooorGang later.

## What's in the box?

When you open your Raspberry Pi, you should have:
- [ ] Raspberry Pi board
- [ ] Power supply (USB-C)
- [ ] Maybe a microSD card (if it came with one)

## What you need to buy/find:

- [ ] MicroSD card (32GB, Class 10) - if not included
- [ ] SD card reader - to flash the OS from your Mac
- [ ] Ethernet cable - easier than WiFi for first setup
- [ ] HDMI cable + monitor + keyboard - OR just use SSH (we'll try SSH first)

## Step 1: Flash the OS to MicroSD Card

1. **Download Raspberry Pi Imager on your Mac**
   - Go to: https://www.raspberrypi.com/software/
   - Click "Download for macOS"
   - Install it

2. **Flash the OS**
   - Insert microSD card into your Mac (using SD card reader)
   - Open Raspberry Pi Imager
   - Click "Choose OS" → "Raspberry Pi OS (64-bit)"
   - Click "Choose Storage" → Select your microSD card
   - **IMPORTANT**: Click the gear icon ⚙️ (bottom right) for settings:
     - ✅ Set hostname: `flooorgang`
     - ✅ Enable SSH → Use password authentication
     - ✅ Set username: `pi`
     - ✅ Set password: `[pick something you'll remember]`
     - ✅ Configure WiFi:
       - SSID: `[your WiFi name]`
       - Password: `[your WiFi password]`
       - Country: `US`
     - ✅ Set timezone: `America/Los_Angeles` (or your timezone)
   - Click "Save"
   - Click "Write" and wait (takes 5-10 minutes)

3. **Eject the microSD card**
   - When done, eject it from your Mac

## Step 2: Boot the Pi

1. **Insert the microSD card into the Pi**
   - The slot is on the bottom of the board
   - Push it in until it clicks

2. **Connect cables**
   - Ethernet cable → Pi → Router (recommended for first boot)
   - Power supply → Pi
   - Pi will boot automatically when powered (red LED = power, green LED = activity)

3. **Wait 1-2 minutes**
   - First boot takes a bit longer
   - Green LED should blink occasionally (means it's doing stuff)

## Step 3: Connect to the Pi

**From your Mac's terminal:**

```bash
# Wait about 2 minutes after plugging in power, then try:
ssh pi@flooorgang.local

# If that doesn't work, find the IP from your router and try:
ssh pi@192.168.1.XXX

# Enter the password you set in Step 1
```

**If you see this:**
```
pi@flooorgang:~ $
```
**YOU'RE IN! 🎉**

## Step 4: Quick Test

Just run these to make sure everything works:

```bash
# Check Python version
python3 --version

# Check internet
ping -c 3 google.com

# Check disk space
df -h

# That's it for Day 1!
```

## Troubleshooting

**Can't SSH with `flooorgang.local`?**
- Try finding the Pi's IP address in your router admin page (usually 192.168.1.1)
- Then: `ssh pi@[IP-ADDRESS]`

**"Host key verification failed"?**
- Run: `ssh-keygen -R flooorgang.local`
- Try SSH again

**"Connection refused"?**
- Make sure you enabled SSH in the Raspberry Pi Imager settings (Step 1)
- Try rebooting the Pi (unplug power, wait 10 seconds, plug back in)

**Green LED not blinking?**
- SD card might not be seated properly - push it in until it clicks
- Try reflashing the SD card

## What's Next?

Once you're successfully SSH'd into the Pi:
- **Day 2**: Update the system and install Python dependencies
- **Day 3**: Clone FlooorGang and test the scanner
- **Day 4**: Set up automated daily runs

But for now, just getting SSH access is the goal!

---

**Shopping list** (if you don't have these):
- MicroSD card 32GB: ~$8 on Amazon
- SD card reader: ~$10 on Amazon
- Ethernet cable: probably have one lying around
