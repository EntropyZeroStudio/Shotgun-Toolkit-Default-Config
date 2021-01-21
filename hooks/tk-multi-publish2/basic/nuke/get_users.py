import os


def get_userID():
    userName = os.environ['USERNAME']
    userDict = {'bgil': 286, 'daniel': 61, 'david': 58, 'dnicolas': 70, 'dperea' : 152, 'hector': 62, 'jaime': 53, 'jordi': 54, 'jalvarez': 72, 'jgomez': 151, 'lgarcia': 118, 'lucia': 63, 'mduque': 187, 'mmartinez': 319, 'pedro': 51, 'pibanez': 153}
    sg_user = userDict.get(userName)
    return sg_user
