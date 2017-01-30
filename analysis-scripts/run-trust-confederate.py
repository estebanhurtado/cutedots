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
    ('.x', [-1.0, 0.0, 0.0], 1),
    ('.y', [0.0, 1.0, 0.0], 1),
    ('', [-1.0, 1.0, 0.0], 2)
]

root = "~/Data/trust2-confederate/"
times = ['before', 'after', 'break']
conditions = ['control-'+t for t in times] + ['exp-'+t for t in times]

batch(root, analyses, conditions)
