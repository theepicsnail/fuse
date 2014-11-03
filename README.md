fuse
====

Fuse filesystem thing

Requirements: python2.7, fuse, redis
```bash
#Clone
git clone https://github.com/theepicsnail/fuse
cd fuse

#Setup
#mkvirtualenv $VIRTUAL_ENV --python=`which python2.7`
virtualenv $VIRTUAL_ENV
source $VIRTUAL_ENV/bin/activate
pip install redis fusepy

#Run
mkdir $MOUNT_POINT
python memory.py $MOUNT_POINT
```
