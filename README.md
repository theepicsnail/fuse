fuse
====

Fuse filesystem thing

Requirements: python2.7, fuse, redis
```bash
#Clone
git clone https://github.com/theepicsnail/fuse
cd fuse

#Setup
mkvirtualenv test --python=`which python2.7`
pip install redis fusepy

#Run
mkdir test
python memory.py test
```
