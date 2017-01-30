import os

def compute(root, condition, append, scale, dof):
    command = "python xcorr.py --infolder " + os.path.join(root, condition) + "/ --outfile " + condition + append
    command += " --scale %f %f %f" % tuple(scale)
    command += " --dof " + str(dof)
    print command
    os.system(command)

def batch(root, analyses, conditions):
    for condition in conditions:
        for append, scale, dof in analyses:
            compute(root, condition, append, scale, dof)


analyses = [
    ('.x', [-1.0, 0.0, 0.0], 3),
    ('.y', [0.0, 1.0, 0.0], 3),
#    ('', [-1.0, 1.0, 1.0], 3)
]

root = "~/Data/trust3-seg/"
times = ['before', 'after']
conditions = ['control-'+t for t in times] + ['exp-'+t for t in times]

batch(root, analyses, conditions)
os.system("mv exp-before.x experimental-before.x")
os.system("mv exp-before.y experimental-before.y")
os.system("mv exp-after.x experimental-after.x")
os.system("mv exp-after.y experimental-after.y")
