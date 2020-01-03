import argparse
import h5py
import os

parser = argparse.ArgumentParser(description='Recursively set cuetdots files framerate.')
parser.add_argument('framerate', type=float,
                    help='New framerate.')

args = parser.parse_args()
newFR = float(args.framerate)

print("Setting framerate to %f." % newFR);


for root, dirs, files in os.walk("."):
    for name in files:
        if name.endswith(".qtd"):
            try:
                with h5py.File(path, "r+") as f:
                    currentFR = f['trajectories'].attrs['frame_rate']
                    f['trajectories'].attrs['frame_rate'] = newFR
                    f.close()
                #print("\tSet framerate from %f to %f." % (currentFR, newFR))
            except:
                path = os.path.join(root, name)
                print(path)
                print("\tCould not set framerate.")

