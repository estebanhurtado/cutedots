import h5py
import os

for root, dirs, files in os.walk("."):
    for name in files:
        if name.endswith(".qtd"):
            path = os.path.join(root, name)
            try:
                with h5py.File(path, "r") as f:
                    currentFR = f['trajectories'].attrs['frame_rate']
                    print(currentFR, path)
            except:
                print(path)
                print("\tCould not read framerate.")

