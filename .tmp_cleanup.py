import os
p = r"D:\Project\1111DIVISION\.tmp_rename_council.py"
if os.path.exists(p):
    os.remove(p)
    print("REMOVED:", p)
else:
    print("NOT FOUND (ok):", p)