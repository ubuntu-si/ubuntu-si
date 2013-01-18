deb64:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F -aamd64 && cd .. && mv si-ubuntu-defaults_* dist
deb32:
	cd si-ubuntu-defaults && dpkg-buildpackage -d -us -uc -F -ai386 && cd .. && mv si-ubuntu-defaults_* dist32
iso64:
	cd dist/ && ubuntu-defaults-image --release precise --arch amd64 --package si-ubuntu-defaults_*_all.deb --components main,restricted,universe
iso32:
	cd dist32/ && ubuntu-defaults-image --release precise --arch i386 --package si-ubuntu-defaults_*_all.deb --components main,restricted,universe
test:
	kvm -m 1024 -cdrom binary.hybrid.iso -boot d 

dist64:
	cd dist/ && buildtorrent binary-hybrid.iso -a "udp://tracker.publicbt.com:80" -w "http://185.14.186.232/dist/binary-hybrid.iso" binary-hybrid.iso.torrent
	cd dist/ && zsyncmake -C -e binary-hybrid.iso

dist32:
	cd dist32/ && buildtorrent binary-hybrid.iso -a "udp://tracker.publicbt.com:80" -w "http://185.14.186.232/dist32/binary-hybrid.iso" binary-hybrid.iso.torrent
	cd dist32/ && zsyncmake -C -e binary-hybrid.iso

.PHONY: deb deb32 iso iso32 test dist dist32