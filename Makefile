deb:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F -aamd64 && cd .. && mv si-ubuntu-defaults_* dist
deb32:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F -ai386 && cd .. && mv si-ubuntu-defaults_* dist32
iso:
	ubuntu-defaults-image --release precise --arch amd64 --package dist/si-ubuntu-defaults_*_all.deb --components main,restricted,universe
iso32:
	ubuntu-defaults-image --release precise --arch i386 --package dist32/si-ubuntu-defaults_*_all.deb --components main,restricted,universe
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -boot d 

dist:
	mv binary-hybrid.iso dist/
	cd dist/
	buildtorrent binary-hybrid.iso -a "udp://tracker.ccc.de:80" -w "http://185.14.186.232/dist/binary-hybrid.iso" binary-hybrid.iso.torrent
	zsyncmake binary-hybrid.iso

dist32:
	mv binary-hybrid.iso dist32/
	cd dist32/
	buildtorrent binary-hybrid.iso -a "udp://tracker.ccc.de:80" -w "http://185.14.186.232/dist32/binary-hybrid.iso" binary-hybrid.iso.torrent
	zsyncmake binary-hybrid.iso

build32:
	deb32 iso32 dist32

build:
	deb iso dist

.PHONY: deb deb32 iso iso32 test dist dist32