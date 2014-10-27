echo "Starting"
ls foo
echo "--"
python memory.py foo &
PGID=$!
echo "$PGID" > PGID
echo $PGID
sleep .1
