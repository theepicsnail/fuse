MOUNT_POINT = mnt_point

all:
	gcc -Wall -o fs src/main.c `pkg-config fuse --cflags --libs`
	@echo "'make mount' to mount"

mount:
	@mkdir $(MOUNT_POINT)
	./fs $(MOUNT_POINT)
	@echo "'make unmount' to unmout"

unmount:
	fusermount -u $(MOUNT_POINT)
	@rmdir $(MOUNT_POINT)
