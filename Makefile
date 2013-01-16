deb:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F && cd .. && mv si-ubuntu-defaults_* dist
iso:
	ubuntu-defaults-image --release precise --package dist/si-ubuntu-defaults_*_all.deb --components main,restricted,universe
iso32:
	ubuntu-defaults-image --release precise --arch i386 --package dist/si-ubuntu-defaults_*_all.deb --components main,restricted,universe
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -boot d 
dist:
	buildtorrent binary-hybrid.iso -a "udp://185.14.184.14:6969" -w "http://185.14.184.14/binary-hybrid.iso" binary-hybrid.iso.torrent
	zsyncmake binary-hybrid.iso
clean:
	rm dist/*

all:
	clean deb iso

.PHONY: deb iso test clean