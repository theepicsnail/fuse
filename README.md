fuse
====

Fuse filesystem thing

Requirements: python2.7, fuse, redis
```bash
#Clone
git clone https://github.com/theepicsnail/fuse
cd fuse

#Setup
#mkvirtualenv test --python=`which python2.7`
virtualenv test
source test/bin/activate
pip install redis fusepy

#Run
mkdir test
python memory.py test
```
