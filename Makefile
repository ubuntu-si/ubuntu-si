deb:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F && cd .. && mv si-ubuntu-defaults_* dist
iso:
	ubuntu-defaults-image --release precise --package dist/si-ubuntu-defaults_*_all.deb --components main,restricted,universe
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -boot d 

clean:
	rm dist/*

all:
	clean deb iso

.PHONY: deb iso test clean