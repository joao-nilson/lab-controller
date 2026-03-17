import ctypes

c = ctypes.CDLL("../hd-debug/hd.so")

class Disk(ctypes.Structure):
    _fields_ = [('disk_temp', ctypes.c_int), 
                ('disk_path', ctypes.c_char_p),
                ('disk_name', ctypes.c_char_p)]

# Set up function signatures
c.get_disk_count.argtypes = []
c.get_disk_count.restype = ctypes.c_int

c.get_disks.argtypes = []
c.get_disks.restype = ctypes.POINTER(Disk)

c.free_disks.argtypes = [ctypes.POINTER(Disk), ctypes.c_int]
c.free_disks.restype = None

# Get disk count
count = c.get_disk_count()
print(f"Number of disks: {count}")

# Get disks array
disks_ptr = c.get_disks()
if not disks_ptr:
    print("Failed to get disks")
    exit(1)

# Convert to Python list
disks = []
for i in range(count):
    disk = disks_ptr[i]
    disks.append({
        'temp': disk.disk_temp,
        'path': disk.disk_path.decode('latin-1') if disk.disk_path else None,
        'name': disk.disk_name.decode('latin-1') if disk.disk_name else None
    })

# Free the C memory
c.free_disks(disks_ptr, count)

# Print results
for idx, disk in enumerate(disks):
    print(f"Disk {idx + 1}:")
    print(f"  Path: {disk['path']}")
    print(f"  Name: {disk['name']}")
    print(f"  Temp: {disk['temp']}°C")
    print()

