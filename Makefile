deb:
	cd siubuntu-defaults && dpkg-buildpackage -d -us -uc -F && cd .. && mv siubuntu-defaults_* dist
iso:
	ubuntu-defaults-image --package dist/siubuntu-defaults_*_all.deb --components main,restricted,universe --arch amd64
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -vga std -sdl

clean:
	rm dist/*

all:
	clean deb iso

.PHONY: deb iso test clean