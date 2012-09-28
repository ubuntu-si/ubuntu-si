deb:
	cd ubuntu-defaults-slovenia && debuild && cd .. && mv ubuntu-defaults-slovenia_* dist
iso:
	ubuntu-defaults-image --package dist/ubuntu-defaults-slovenia_*_all.deb --components main,restricted,universe
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -vga std -sdl
zsync:
	zsyncmake binary.hybrid.iso -u binary.hybrid.iso

clean:
	rm -rf .build auto cache chroot config local binary.log ubuntu-defaults-slovenia/debian/ubuntu-defaults-slovenia*

all:
	iso zsync

.PHONY: deb iso test zsync clean