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


root = "~/Data/en_seg/"
analyses = [
    ('.x', [-1.0, 0.0, 0.0], 1),
    ('.y', [0.0, 1.0, 0.0], 1),
    ('', [-1.0, 1.0, 0.0], 2)
]
conditions = ['E', 'N']

batch(root, analyses, conditions)

root = "~/Data/trust_seg/"
conditions = ['trust', 'distrust', 'break']

batch(root, analyses, conditions)

